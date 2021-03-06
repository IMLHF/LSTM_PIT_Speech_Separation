# run without TFRecord, more efficient.
import argparse
import os
import sys
# import sys.stdout
import time
import numpy as np
import tensorflow as tf
from models.lstm_pit import LSTM
import utils
import utils.tf_tool
import wave
import shutil
import traceback
from dataManager.mixed_aishell_tfrecord_io import get_batch_use_queue, generate_tfrecord, rmNormalization
from dataManager import mixed_aishell_tfrecord_io as wav_tool
from tensorflow.python.client import timeline
from FLAGS import NNET_PARAM
from FLAGS import MIXED_AISHELL_PARAM


os.environ['CUDA_VISIBLE_DEVICES'] = sys.argv[1]


def decode():
  tf.logging.info("Go to 'run_lstm_pit_tfdata.py'.")


def train_one_epoch(sess, tr_model, i_epoch, run_metadata):
  """Runs the model one epoch on given data."""
  tr_loss, i = 0, 0
  stime = time.time()
  while True:
    try:
      if NNET_PARAM.time_line:
        _, loss, current_batchsize = sess.run(
            [tr_model.train_op, tr_model.loss, tr_model.batch_size],
            options=tf.RunOptions(trace_level=tf.RunOptions.FULL_TRACE),
            run_metadata=run_metadata)
      else:
        _, loss, current_batchsize = sess.run(
            [tr_model.train_op, tr_model.loss, tr_model.batch_size])
      tr_loss += loss
      if (i+1) % NNET_PARAM.minibatch_size == 0:
        if NNET_PARAM.time_line and NNET_PARAM.timeline_type == 'minibatch':
          tl = timeline.Timeline(run_metadata.step_stats)
          ctf = tl.generate_chrome_trace_format()
          with open('_timeline/%03dtimeline%04d.json' % (i_epoch, i+1), 'w') as f:
            f.write(ctf)
        lr = sess.run(tr_model.lr)
        costtime = time.time()-stime
        stime = time.time()
        print("MINIBATCH %05d: TRAIN AVG.LOSS %04.6f, "
              "(learning rate %02.6f)" % (
                  i + 1, tr_loss / (i*NNET_PARAM.batch_size+current_batchsize), lr), 'cost time: %06dS' % costtime)
        sys.stdout.flush()
      i += 1
    except tf.errors.OutOfRangeError:
      break
  tr_loss /= ((i-1)*NNET_PARAM.batch_size+current_batchsize)
  return tr_loss


def eval_one_epoch(sess, val_model, run_metadata):
  """Cross validate the model on given data."""
  val_loss = 0
  data_len = 0
  while True:
    try:
      if NNET_PARAM.time_line:
        loss, current_batchsize = sess.run(
            [val_model.loss, val_model.batch_size],
            options=tf.RunOptions(trace_level=tf.RunOptions.FULL_TRACE),
            run_metadata=run_metadata)
      else:
        loss, current_batchsize = sess.run(
            [val_model.loss, val_model.batch_size])
      val_loss += loss
      data_len += current_batchsize
    except tf.errors.OutOfRangeError:
      break
  val_loss /= data_len
  return val_loss


def train():

  g = tf.Graph()
  with g.as_default():
    with tf.device('/cpu:0'):
      with tf.name_scope('input'):
        # region TFRecord+DataSet
        train_tfrecords, val_tfrecords, testcc_tfrecords = generate_tfrecord(
            gen=MIXED_AISHELL_PARAM.GENERATE_TFRECORD)
        if MIXED_AISHELL_PARAM.GENERATE_TFRECORD:
          exit(0)  # set gen=True and exit to generate tfrecords
        x_batch_tr, y1_batch_tr, y2_batch_tr, lengths_batch_tr = get_batch_use_queue(
            train_tfrecords)
        x_batch_val, y1_batch_val, y2_batch_val, lengths_batch_val = get_batch_use_queue(
            val_tfrecords)
        # endregion
    with tf.name_scope('model'):
      tr_model = LSTM(x_batch_tr,
                      y1_batch_tr,
                      y2_batch_tr,
                      lengths_batch_tr)
      tf.get_variable_scope().reuse_variables()
      val_model = LSTM(x_batch_val,
                       y1_batch_val,
                       y2_batch_val,
                       lengths_batch_val)

    utils.tf_tool.show_all_variables()
    init = tf.group(tf.global_variables_initializer(),
                    tf.local_variables_initializer())
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = NNET_PARAM.GPU_RAM_ALLOW_GROWTH
    config.allow_soft_placement = True
    sess = tf.Session(config=config)
    sess.run(init)
    if NNET_PARAM.resume_training.lower() == 'true':
      ckpt = tf.train.get_checkpoint_state(NNET_PARAM.save_dir + '/nnet')
      if ckpt and ckpt.model_checkpoint_path:
        tf.logging.info("restore from" + ckpt.model_checkpoint_path)
        tr_model.saver.restore(sess, ckpt.model_checkpoint_path)
        best_path = ckpt.model_checkpoint_path
      else:
        tf.logging.info("checkpoint not found")
        exit(-1)
    # g.finalize()

    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(sess=sess, coord=coord)
    try:
      # validation before training.
      run_metadata = None
      if NNET_PARAM.time_line:
        run_metadata = tf.RunMetadata()
        if os.path.exists('_timeline'):
          shutil.rmtree('_timeline')
        os.mkdir('_timeline')
      # sess.run(iter_val.initializer)
      start_time = time.time()
      print('shape')
      print(sess.run([tf.shape(x_batch_val), tf.shape(y1_batch_val),
                      tf.shape(y2_batch_val), tf.shape(lengths_batch_val)]))
      print('time prepare valdata :', time.time()-start_time)
      loss_prev = eval_one_epoch(sess,
                                 val_model,
                                 run_metadata)
      tf.logging.info("CROSSVAL PRERUN AVG.LOSS %.4FS  costime %d" %
                      (loss_prev, time.time()-start_time))

      tr_model.assign_lr(sess, NNET_PARAM.learning_rate)
      reject_num = 0
      for epoch in range(NNET_PARAM.max_epochs):
        # sess.run([iter_train.initializer, iter_val.initializer])
        start_time = time.time()
        # Training
        # print('shape')
        # print(sess.run([tf.shape(x_batch_tr), tf.shape(y1_batch_tr),
        #                 tf.shape(y2_batch_tr), tf.shape(lengths_batch_tr)]))
        # print('time prepare trdata :', time.time()-start_time)
        tr_loss = train_one_epoch(sess,
                                  tr_model,
                                  epoch,
                                  run_metadata)
        # exit(0)

        # Validation
        val_loss = eval_one_epoch(sess,
                                  val_model,
                                  run_metadata)

        end_time = time.time()
        # Determine checkpoint path
        ckpt_name = "nnet_iter%d_lrate%e_trloss%.4f_cvloss%.4f_costtime%dS" % (
            epoch + 1, NNET_PARAM.learning_rate, tr_loss, val_loss, end_time - start_time)
        ckpt_dir = NNET_PARAM.save_dir + '/nnet'
        if not os.path.exists(ckpt_dir):
          os.makedirs(ckpt_dir)
        ckpt_path = os.path.join(ckpt_dir, ckpt_name)
        # Relative loss between previous and current val_loss
        rel_impr = np.abs(loss_prev - val_loss) / loss_prev
        # Accept or reject new parameters
        if val_loss < loss_prev:
          reject_num = 0
          tr_model.saver.save(sess, ckpt_path)
          # Logging train loss along with validation loss
          loss_prev = val_loss
          best_path = ckpt_path
          tf.logging.info(
              "ITERATION %03d: TRAIN AVG.LOSS %.4f, (lrate%e) CROSSVAL"
              " AVG.LOSS %.4f, %s (%s), TIME USED: %.2fs" % (
                  epoch + 1, tr_loss, NNET_PARAM.learning_rate, val_loss,
                  "nnet accepted", ckpt_name,
                  (end_time - start_time) / 1))
        else:
          reject_num += 1
          tr_model.saver.restore(sess, best_path)
          tf.logging.info(
              "ITERATION %03d: TRAIN AVG.LOSS %.4f, (lrate%e) CROSSVAL"
              " AVG.LOSS %.4f, %s, (%s), TIME USED: %.2fs" % (
                  epoch + 1, tr_loss, NNET_PARAM.learning_rate, val_loss,
                  "nnet rejected", ckpt_name,
                  (end_time - start_time) / 1))

        # Start halving when improvement is low
        if (rel_impr < NNET_PARAM.start_halving_impr) or (reject_num >= 3):
          reject_num = 0
          NNET_PARAM.learning_rate *= NNET_PARAM.halving_factor
          tr_model.assign_lr(sess, NNET_PARAM.learning_rate)

        # Stopping criterion
        if rel_impr < NNET_PARAM.end_halving_impr:
          if epoch < NNET_PARAM.min_epochs:
            tf.logging.info(
                "we were supposed to finish, but we continue as "
                "min_epochs : %s" % NNET_PARAM.min_epochs)
            continue
          else:
            tf.logging.info(
                "finished, too small rel. improvement %g" % rel_impr)
            break

        # save timeline
        if NNET_PARAM.time_line and NNET_PARAM.timeline_type == 'epoch':
          tl = timeline.Timeline(run_metadata.step_stats)
          ctf = tl.generate_chrome_trace_format()
          with open('_timeline/%03dtimeline.json' % (epoch,), 'w') as f:
            f.write(ctf)

    except Exception as e:
      # Report exceptions to the coordinator.
      coord.request_stop(e)
    finally:
      # Terminate as usual.  It is innocuous to request stop twice.
      coord.request_stop()
      # Wait for threads to finish.
      coord.join(threads)

    sess.close()
    tf.logging.info("Done training")


def main(_):
  if not os.path.exists(NNET_PARAM.save_dir):
    os.makedirs(NNET_PARAM.save_dir)
  if NNET_PARAM.decode:
    decode()
  else:
    train()


if __name__ == "__main__":
  tf.logging.set_verbosity(tf.logging.INFO)
  tf.app.run(main=main)
