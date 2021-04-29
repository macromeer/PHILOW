import datetime
import os
import sys
from pathlib import Path

import dask_image.imread
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QSizePolicy, QHBoxLayout, QLabel, QFileDialog, \
    QVBoxLayout
from skimage.filters import gaussian
from skimage import io


# 値を-1から1に正規化する関数
def normalize_x(image):
    image = image/127.5 - 1
    return image


# 値を0から1に正規化する関数
def normalize_y(image):
    image = image/255
    return image


# 値を0から255に戻す関数
def denormalize_y(image):
    image = image*255
    return image


def annotation_to_input(label_ermito):
    mito = (label_ermito == 1)*255
    er = (label_ermito == 2)*255
    mito = normalize_y(mito)
    er = normalize_y(er)
    mito_anno = np.zeros_like(mito)
    er_anno = np.zeros_like(er)
    mito = gaussian(mito, sigma=2)*255
    er = gaussian(er, sigma=2) * 255
    mito_anno[:, :] = mito
    er_anno[:, :] = er
    anno = np.concatenate([mito_anno[:, :, np.newaxis], er_anno[:, :, np.newaxis]], 2)
    anno = normalize_x(anno[np.newaxis, :, :, :])
    return anno


def check_csv(project_path, ext):
    if not os.path.isfile(os.path.join(project_path, os.path.basename(project_path) + '.csv')):
        cols = ['project', 'type', 'ext', 'z', 'y',	'x', 'z_size', 'y_size', 'x_size', 'created_date', 'update_date',
                'path', 'notes']
        df = pd.DataFrame(index=[], columns=cols)
        filename_pattern_original = os.path.join(project_path, f'dataset/Original_size/Original/*{ext}')
        images_original = dask_image.imread.imread(filename_pattern_original)
        z, y, x = images_original.shape
        record = pd.Series([os.path.basename(project_path), 'dataset', '.tif', 0, 0, 0, z, y, x, datetime.datetime.now(),
                            '', os.path.join(project_path, 'dataset/Original_size/Original'), ''], index=df.columns)
        df = df.append(record, ignore_index=True)
        df.to_csv(os.path.join(project_path, os.path.basename(project_path) + '.csv'))
    else:
        pass


def check_annotations_dir(project_path):
    if not os.path.isdir(os.path.join(project_path, 'annotations/Original_size/master')):
        os.makedirs(os.path.join(project_path, 'annotations/Original_size/master'))
    else:
        pass


def check_zarr(project_path, ext):
    if not len(list((Path(project_path) / 'dataset' / 'Original_size').glob('./*.zarr'))):
        filename_pattern_original = os.path.join(project_path, f'dataset/Original_size/Original/*{ext}')
        images_original = dask_image.imread.imread(filename_pattern_original)
        images_original.to_zarr(os.path.join(project_path, f'dataset/Original_size/Original.zarr'))
    else:
        pass


def check(project_path, ext):
    check_csv(project_path, ext)
    check_zarr(project_path, ext)
    check_annotations_dir(project_path)


def load_images(directory):
    filename_pattern_original = os.path.join(directory, '*png')
    images_original = dask_image.imread.imread(filename_pattern_original)
    return images_original


def load_predicted_masks(mito_mask_dir, er_mask_dir):
    filename_pattern_mito_label = os.path.join(mito_mask_dir, '*png')
    filename_pattern_er_label = os.path.join(er_mask_dir, '*png')
    images_mito_label = dask_image.imread.imread(filename_pattern_mito_label)
    images_mito_label = images_mito_label.compute()
    images_er_label = dask_image.imread.imread(filename_pattern_er_label)
    images_er_label = images_er_label.compute()
    base_label = (images_mito_label > 127) * 1 + (images_er_label > 127) * 2
    return base_label


def load_saved_masks(mod_mask_dir):
    filename_pattern_label = os.path.join(mod_mask_dir, '*png')
    images_label = dask_image.imread.imread(filename_pattern_label)
    images_label = images_label.compute()
    base_label = images_label
    return base_label


def load_raw_masks(raw_mask_dir):
    filename_pattern_raw = os.path.join(raw_mask_dir, '*png')
    images_raw = dask_image.imread.imread(filename_pattern_raw)
    images_raw = images_raw.compute()
    base_label = np.where((126 < images_raw) & (images_raw < 171), 255, 0)
    return base_label

'''
def save_annotations(labels):
    class App(QWidget):
        def __init__(self):
            super().__init__()
            self.out_path = ""
            self.btn1 = QPushButton('Select', self)
            self.btn1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.btn1.clicked.connect(self.show_dialog_out)
            self.btn2 = QPushButton('Save', self)
            self.btn2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.btn2.clicked.connect(self.save_masks)
            self.lbl1 = QLabel('save dir', self)
            self.labels = labels
            self.build()

        def build(self):
            box = QVBoxLayout()
            box.addWidget(combine_blocks(self.btn1, self.lbl1))
            box.addWidget(self.btn2)

            self.setLayout(box)
            self.show()

        def show_dialog_out(self):
            default_path = max(self.opath, self.modpath, os.path.expanduser('~'))
            f_name = QFileDialog.getExistingDirectory(self, 'Select Directory', default_path)
            if f_name:
                self.out_path = f_name
                self.lbl1.setText(self.out_path)

        def save_masks(self):
            num = self.labels.shape[0]
            for i in range(num):
                label = self.labels[i]
                io.imsave(os.path.join(self.out_path, str(i).zfill(4) + '.png'), label)

    app = QApplication(sys.argv)
    ex1 = App()
    ex1.show()
    app.exec()
'''


def combine_blocks(block1, block2):
    temp_widget = QWidget()
    temp_layout = QHBoxLayout()
    temp_layout.addWidget(block1)
    temp_layout.addWidget(block2)
    temp_widget.setLayout(temp_layout)
    return temp_widget


def save_masks(labels, out_path):
    num = labels.shape[0]
    os.makedirs(out_path, exist_ok=True)
    for i in range(num):
        label = labels[i]
        io.imsave(os.path.join(out_path, str(i).zfill(4) + '.png'), label)
