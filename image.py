################################################################################
#
# Copyright (c) 2017 University of Oxford
# Authors:
#  Geoff Pascoe (gmp@robots.ox.ac.uk)
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 4.0 International License.
# To view a copy of this license, visit
# http://creativecommons.org/licenses/by-nc-sa/4.0/ or send a letter to
# Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.
#
###############################################################################

import re
from PIL import Image
from colour_demosaicing import demosaicing_CFA_Bayer_bilinear as demosaic
import numpy as np

BAYER_STEREO = 'gbrg'
BAYER_MONO = 'rggb'


def load_image(image_path, model=None):
    """Loads and rectifies an image from file.

    Args:
        image_path (str): path to an image from the dataset.
        model (camera_model.CameraModel): if supplied, model will be used to undistort image.

    Returns:
        numpy.ndarray: demosaiced and optionally undistorted image

    """
    if model:
        camera = model.camera
    else:
        camera = re.search('(stereo|mono_(left|right|rear))', image_path).group(0)
    if camera == 'stereo':
        pattern = BAYER_STEREO
    else:
        pattern = BAYER_MONO
        

    img = Image.open(image_path)
    img = demosaic(img, pattern)
    if model:
        img = model.undistort(img)

    return np.array(img).astype(np.uint8)


if __name__ == '__main__':

    # Play undistorce image
    
    import os
    import argparse
    import cv2
    import time
    from datetime import datetime as dt
    from camera_model import CameraModel

    import my_params

    parser = argparse.ArgumentParser(description='Preprocess and save all images')
    parser.add_argument('--dir', type=str, default=my_params.image_dir, 
                        help='Directory containing images.')
    parser.add_argument('--models_dir', type=str, default=my_params.model_dir, 
                        help='(optional) Directory containing camera model. If supplied, images will be undistorted before display')
    parser.add_argument('--scale', type=float, default=0.1, 
                        help='(optional) factor by which to scale images before display')
    args = parser.parse_args()

    # Set argument
    # args.scale = 0.2

    frames = 0
    start = time.time() 

    camera = re.search('(stereo|mono_(left|right|rear))', args.dir).group(0)

    timestamps_path = os.path.join(os.path.join(args.dir, os.pardir, camera + '.timestamps'))
    print(timestamps_path)
    if not os.path.isfile(timestamps_path):
        timestamps_path = os.path.join(args.dir, os.pardir, os.pardir, camera + '.timestamps')
        if not os.path.isfile(timestamps_path):
            raise IOError("Could not find timestamps file")

    model = CameraModel(args.models_dir, args.dir)

    current_chunk = 0
    timestamps_file = open(timestamps_path)
    for line in timestamps_file:
        tokens = line.split()
        datetime = dt.utcfromtimestamp(int(tokens[0])/1000000)
        chunk = int(tokens[1])

        filename = os.path.join(args.dir, tokens[0] + '.png')
        if not os.path.isfile(filename):
            if chunk != current_chunk:
                print("Chunk " + str(chunk) + " not found")
                current_chunk = chunk
            continue

        current_chunk = chunk

        img = load_image(filename, model)
        # print(img.shape)
    
        # save image
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        cv2.imwrite(my_params.reprocess_image_dir + '//' + tokens[0] + '.png', img)

        width = int(img.shape[1] * args.scale)
        height = int(img.shape[0] * args.scale)
        dim = (width, height)
        # resize image
        img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)

        # cv2.imshow("img",img)
        # key = cv2.waitKey(0)
        # if key & 0xFF == ord('q'):
        #     break
        frames += 1

        print(datetime)
        print("FPS of the video is {:5.2f}".format( frames / (time.time() - start)))
        
