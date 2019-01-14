# -*- coding: utf-8 -*-

import os
import numpy as np
import SimpleITK as sitk
import matplotlib.pyplot as plt


class NotDeterminedBySITKException(Exception):
    pass


class NotSavedByPILException(Exception):
    pass


class Conversion:

    def __init__(self, input_dicom, output_dir):
        self.input_dicom = input_dicom
        self.data = sitk.ReadImage(self.input_dicom)
        self.img = sitk.GetArrayFromImage(self.data)
        self.output_dir = output_dir
        self.image_format = None

    def determine_image_format(self):
        # DICOM タグから画像フォーマットを判別
        if self.img.ndim == 3:
            # モノクロの場合は次元が小さい
            self.image_format = 'monochrome'
        if self.img.ndim == 4:
            if 'PALETTE' in self.data.GetMetaData('0028|0004'):
                self.image_format = 'palette'
            elif 'RGB' in self.data.GetMetaData('0028|0004'):
                self.image_format = 'rgb'
            elif 'YBR_FULL' in self.data.GetMetaData('0028|0004'):
                self.image_format = 'ybr_full'
            elif 'YBR_PARTIAL_422' in self.data.GetMetaData('0028|0004') \
                    or 'YBR_PARTIAL_420' in self.data.GetMetaData('0028|0004'):
                # 実はここの判別が調査不足
                self.image_format = 'ybr_partial'
            elif 'YBR_ICT' in self.data.GetMetaData('0028|0004'):
                self.image_format = 'ybr_ict'
            elif 'YBR_RCT' in self.data.GetMetaData('0028|0004'):
                self.image_format = 'ybr_rct'
        if self.image_format is None:
            raise NotDeterminedBySITKException

    def pickup_image(self):
        if self.image_format == 'monochrome':
            all_keys = self.data.GetMetaDataKeys()
            # np.set_printoptions(threshold=np.inf)
            # print(self.img)
            for image in self.img:
                # print(image)
                i = 0
                if '0028|0004' in all_keys and 'MONOCHROME1' in self.data.GetMetaData('0028|0004'):
                    cmap = 'binary'
                else:
                    cmap = 'binary_r'
                bits_stored = self.data.GetMetaData('0028|0101')
                high_bits = self.data.GetMetaData('0028|0102')
                pr = self.data.GetMetaData('0028|0103')  # 0 は符号なし、1は符号あり
                right_shift = int(high_bits) + 1 - int(bits_stored)
                if right_shift > 0:
                    image = np.right_shift(image, right_shift)
                # WW/WL （画像化に使用する値の範囲）を取得
                try:
                    ww = round(float(self.data.GetMetaData('0028|1051')))
                except:
                    ww = None
                try:
                    wl = round(float(self.data.GetMetaData('0028|1050')))
                except:
                    wl = None
                if ww is not None and wl is not None:
                    max = round(wl + ww / 2)
                    min = round(wl - ww / 2)
                else:
                    u"外れ値を除外して最大値・最小値を得る"
                    min, max = Convert.get_trimed_range(img[0])
                fig = plt.imshow(image, cmap=cmap, vmin=min, vmax=max, interpolation='nearest')
                plt.axis('off')
                fig.axes.get_xaxis().set_visible(False)
                fig.axes.get_yaxis().set_visible(False)
                output_jpg = os.path.join(self.output_dir, str(i) + '.jpg')
                plt.savefig(output_jpg, bbox_inches='tight', pad_inches=0.0)
                plt.clf()
                i += 1
                
        elif self.image_format == 'palette':
            for image in self.img:
                i = 0
                fig = plt.imshow(image, interpolation='nearest')
                plt.axis('off')
                fig.axes.get_xaxis().set_visible(False)
                fig.axes.get_yaxis().set_visible(False)
                output_jpg = os.path.join(self.output_dir, str(i) + '.jpg')
                plt.savefig(output_jpg, bbox_inches='tight', pad_inches=0.0)
                plt.clf()
                i += 1
        else:
            for image in self.img:
                i = 0
                pil_img = None
                if 'ybr' in self.image_format:
                    pil_img = Image.fromarray(np.uint8(image), mode='YCbCr')
                elif self.image_format == 'rgb':
                    pil_img = Image.fromarray(np.uint8(image), mode='RGB')

                if pil_img is not None:
                    output_jpg = os.path.join(self.output_dir, str(i) + '.jpg')
                    pil_img.save(output_jpg, 'JPEG', quality=100, optimize=True)
                else:
                    raise NotSavedByPILException
                i += 1

    @staticmethod
    def get_trimed_range(ar: np.ndarray):
        # 外れ値を除いた最大・最小値を返す
        av = np.mean(ar) # 平均
        sd = np.std(ar) # 標準偏差
        u"外れ値の基準点 3σ"
        outlier_min = av - (sd) * 3
        outlier_max = av + (sd) * 3

        new_ar = ar[(ar <= outlier_max) & (ar >= outlier_min)]
        np.set_printoptions(threshold=np.inf)
        return new_ar.min(), new_ar.max()


if __name__ == '__main__':
    conversion = Conversion('dicom/CT-MONO2-16-ankle', 'jpg')
    conversion.determine_image_format()
    conversion.pickup_image()
