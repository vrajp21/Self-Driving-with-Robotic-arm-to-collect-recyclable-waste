

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import sys
import time
import os
import numpy as np
import tensorflow as tf

def load_graph(model_file):
  graph = tf.Graph()
  graph_def = tf.compat.v1.GraphDef()

  with open(model_file, "rb") as f:
    graph_def.ParseFromString(f.read())
  with graph.as_default():
    tf.import_graph_def(graph_def)

  return graph

def read_tensor_from_image_file(file_name, input_height=299, input_width=299,
				input_mean=0, input_std=255):
  input_name = "file_reader"
  output_name = "normalized"
  file_reader = tf.io.read_file(file_name, input_name)
  if file_name.endswith(".png"):
    image_reader = tf.image.decode_png(file_reader, channels = 3,
                                       name='png_reader')
  elif file_name.endswith(".gif"):
    image_reader = tf.squeeze(tf.image.decode_gif(file_reader,
                                                  name='gif_reader'))
  elif file_name.endswith(".bmp"):
    image_reader = tf.image.decode_bmp(file_reader, name='bmp_reader')
  else:
    image_reader = tf.image.decode_jpeg(file_reader, channels = 3,
                                        name='jpeg_reader')
  float_caster = tf.cast(image_reader, tf.float32)
  dims_expander = tf.expand_dims(float_caster, 0);
  resized = tf.compat.v1.image.resize_bilinear(dims_expander, [input_height, input_width])
  normalized = tf.divide(tf.subtract(resized, [input_mean]), [input_std])
  sess = tf.compat.v1.Session()
  result = sess.run(normalized)

  return result

def load_labels(label_file):
  label = []
  proto_as_ascii_lines = tf.io.gfile.GFile(label_file).readlines()
  for l in proto_as_ascii_lines:
    label.append(l.rstrip())
  return label


def identification(file_name):
  #file_name = "tf_files/flower_photos/daisy/3475870145_685a19116d.jpg"

  label_file = "retrained_labels.txt"
  THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
  label_file = os.path.join(THIS_FOLDER, 'retrained_labels.txt')
  model_files = os.path.join(THIS_FOLDER, 'retrained_graph_20-05-2018.pb')
  input_height = 299
  input_width = 299
  input_mean = 0
  input_std = 255
  input_layer = "Mul"
  output_layer = "final_result"
  os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


  graph = load_graph(model_files)
  t = read_tensor_from_image_file(file_name,
                                  input_height=input_height,
                                  input_width=input_width,
                                  input_mean=input_mean,
                                  input_std=input_std)

  input_name = "import/" + input_layer
  output_name = "import/" + output_layer
  input_operation = graph.get_operation_by_name(input_name);
  output_operation = graph.get_operation_by_name(output_name);

  with tf.compat.v1.Session(graph=graph) as sess:
    #start = time.time()
    results = sess.run(output_operation.outputs[0],
                      {input_operation.outputs[0]: t})
    #end=time.time()
  results = np.squeeze(results)

  top_k = results.argsort()[-5:][::-1]
  labels = load_labels(label_file)

  #print('\nEvaluation time (1-image): {:.3f}s\n'.format(end-start))

  output_result={'bio':results[0],'nonbio':results[1]}
  return(output_result)

  '''if results[0]>results[1]:
    print(str(labels[0])+" "+str(results[0]))
    return("l")
  print(str(labels[1])+" "+str(results[1]))
  return("r")'''


