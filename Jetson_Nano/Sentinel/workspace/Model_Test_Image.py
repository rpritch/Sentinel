import cv2
import object_detection
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util
import numpy as np
import tensorflow as tf


LABEL_FILENAME = 'annotations/labelmap.pbtxt'

MODEL_FILENAME = 'Models/ssd_mobilenet_v2_graph/frozen_inference_graph.pb'

NUM_CLASSES= 4 # WHITE, YELLOW, BUD, POD
cv2.CAP_PROP_FRAME_WIDTH

label_map = label_map_util.load_labelmap(LABEL_FILENAME)
categories = label_map_util.convert_label_map_to_categories(label_map,max_num_classes=NUM_CLASSES,use_display_name = True)
category_index = label_map_util.create_category_index(categories)

config = tf.ConfigProto()
config.gpu_options.allow_growth = True


detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(MODEL_FILENAME,'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')
    
    sess = tf.Session(graph=detection_graph, config=config)

# Input tensor is the image
image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

# Output tensors are the detection boxes, scores, and classes
# Each box represents a part of the image where a particular object was detected
detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

# Each score represents level of confidence for each of the objects.
# The score is shown on the result image, together with the class label.
detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')

# Number of objects detected
num_detections = detection_graph.get_tensor_by_name('num_detections:0')

# while True:
frame = cv2.imread("images/s6493.jpg")
frame = cv2.resize(frame,(300,300), interpolation=cv2.INTER_AREA)
frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
frame_expanded = np.expand_dims(frame_rgb,axis=0)
(boxes, scores, classes, num) = sess.run(
        [detection_boxes, detection_scores, detection_classes, num_detections],
        feed_dict={image_tensor: frame_expanded})

vis_util.visualize_boxes_and_labels_on_image_array(
        frame,
        np.squeeze(boxes),
        np.squeeze(classes).astype(np.int32),
        np.squeeze(scores),
        category_index,
        use_normalized_coordinates=True,
        line_thickness=8,
        min_score_thresh=0.97)
cv2.imwrite("s148_yellow.jpg", frame)
    # cv2.imshow("Object Detect", frame)
    # keyCode = cv2.waitKey(5) &  0xFFF
    # if keyCode == 27:
    #     break
cv2.destroyAllWindows()