import tensorflow as tf


class NNET_PARAM:
  '''
  @decode
  Flag indicating decoding or training.
  Show (mixed_wav, mixed_wav_spec, cleaned_wav, cleaned_wav_pic, cleaned_wav_spec).
  wav_pic is oscillograph.
  wav_spec is spectrum
  '''
  decode = 1
  '''
  @decode_show_more
  Flag indicating show  (label_wav, label_wav_spec, label_wav_pic) or not.
  wav_pic is oscillograph.
  wav_spec is spectrum
  '''
  decode_show_more = 1
  decode_input_norm_speaker_volume = False
  decode_output_norm_speaker_volume = True
  decode_speaker_tracing = True
  # Flag indicating whether to resume training from cptk.
  resume_training = 'false'
  start_epoch = 0
  input_size = 257  # The dimension of input.
  output_size = 257  # The dimension of output per speaker.
  rnn_size = 496  # Number of rnn units to use.
  rnn_num_layers = 2  # Number of layer of rnn model.
  batch_size = 256
  learning_rate = 0.001  # Initial learning rate.
  min_epochs = 10  # Min number of epochs to run trainer without halving.
  max_epochs = 50  # Max number of epochs to run trainer totally.
  halving_factor = 0.7  # Factor for halving.
  # Halving when ralative loss is lower than start_halving_impr.
  start_halving_impr = 0.003
  # Stop when relative loss is lower than end_halving_impr.
  end_halving_impr = 0.0005
  # The num of threads to read tfrecords files.
  num_threads_processing_data = 64
  save_dir = 'exp/lstm_pit'  # Directory to put the train result.
  keep_prob = 0.8  # Keep probability for training dropout.
  max_grad_norm = 5.0  # The max gradient normalization.
  model_type = 'BLSTM'  # BLSTM or LSTM
  LSTM_ACTIVATION = tf.nn.tanh
  # LSTM_ACTIVATION = tf.nn.softmax
  MASK_TYPE = 'IAM'  # IAM: ideal_amplitude_mask; PSM: phase_sensitive_mask.
  # MASK_TYPE='PSM'

  GPU_RAM_ALLOW_GROWTH = True
  USE_MULTIGPU = False  # dont't use multiGPU,because it is not work now...
  GPU_LIST = [0, 2]
  if USE_MULTIGPU:
    if batch_size % len(GPU_LIST) == 0:
      batch_size //= len(GPU_LIST)
    else:
      print('Batch_size %d cannot divided by gpu num %d.' %
            (batch_size, len(GPU_LIST)))
      exit(-1)

  minibatch_size = 400  # batch num to show
  # generate timeline file. # !!! timeling is not work now, so set it false unless to test it.
  time_line = False
  timeline_type = 'minibatch'  # timeline write method. 'epoch' ro 'minibatch'
  RESTORE_PHASE = 'GRIFFIN_LIM'  # 'MIXED','CLEANED','GRIFFIN_LIM'
  GRIFFIN_ITERNUM = 100


class MIXED_AISHELL_PARAM:
  # rawdata, dirs by speakerid, like "....data_aishell/wav/train".
  RAW_DATA = '/home/student/work/pit_test/data'
  DATA_DICT_DIR = '_data/mixed_aishell'
  GENERATE_TFRECORD = False
  PROCESS_NUM_GENERATE_TFERCORD = 64
  SHUFFLE = False

  '''
  TFRECORDS_DIR='/big-data/tmplhf/pit-data/feature_tfrecords_utt03s'
  TFRECORDS_FILE_TYPE='small' # 'big' or 'small'.if 'small', one file per record.
  LEN_WAWE_PAD_TO = 16000*3 # Mixed wave length (16000*3 is 3 seconds)
  UTT_SEG_FOR_MIX = [260, 290]  # Separate utt to [0:260],[260,290],[290:end]
  DATASET_NAMES = ['train', 'validation', 'test_cc']
  DATASET_SIZES = [1400000, 18000, 180000]
  '''
  # TFRECORDS_DIR = '/workspace/alldata/pit-data/feature_tfrecords_utt03s_big' # for docker
  TFRECORDS_DIR = '/ntfs/tmplhf/pit-data/feature_tfrecords_utt03s_big'
  # 'big' or 'small'.if 'small', one file per record.
  TFRECORDS_FILE_TYPE = 'big'
  LEN_WAWE_PAD_TO = 16000*3  # Mixed wave length (16000*3 is 3 seconds)
  UTT_SEG_FOR_MIX = [260, 290]  # Separate utt to [0:260],[260,290],[290:end]
  DATASET_NAMES = ['train', 'validation', 'test_cc']
  DATASET_SIZES = [1400000, 18000, 180000]

  '''
  TFRECORDS_DIR = '/big-data/tmplhf/pit-data/feature_tfrecords_utt10s'
  TFRECORDS_FILE_TYPE='small' # 'big' or 'small'.if 'small', one file per record.
  LEN_WAWE_PAD_TO = 16000*10 # Mixed wave length (16000*3 is 3 seconds)
  UTT_SEG_FOR_MIX = [260, 290]  # Separate utt to [0:260],[260,290],[290:end]
  DATASET_NAMES = ['train', 'validation', 'test_cc']
  DATASET_SIZES = [405600, 5400, 20000]
  '''
  '''
  TFRECORDS_DIR='/ntfs/tmplhf/pit-data/feature_tfrecords_utt10s_big'
  TFRECORDS_FILE_TYPE='big' # 'big' or 'small'.if 'small', one file per record.
  LEN_WAWE_PAD_TO = 16000*10 # Mixed wave length (16000*3 is 3 seconds)
  UTT_SEG_FOR_MIX = [260, 290]  # Separate utt to [0:260],[260,290],[290:end]
  DATASET_NAMES = ['train', 'validation', 'test_cc']
  DATASET_SIZES = [405600, 5400, 20000]
  '''

  # WAVE_NORM=True
  WAVE_NORM = False
  LOG_NORM_MAX = 5
  LOG_NORM_MIN = -3
  NFFT = 512
  OVERLAP = 256
  FS = 16000
