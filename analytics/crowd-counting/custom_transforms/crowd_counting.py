import gstgva
import numpy
import time
import json
from PIL import Image, ImageDraw

class CrowdCounting:
    def __init__(self,width=0,height=0,zonemap=[]):
        self.zone = []
        self.mask = []
        self.crowd_count = []
        self.polygon = []

        for z in range(len(zonemap)):
            self.zone.append(zonemap[z]["zone"])
            self.mask.append([])
            self.crowd_count.append(0)
            self.polygon.append([])
            
            for sublist in zonemap[z]["polygon"]:
                for item in sublist:
                    self.polygon[z].append(item)

        self.sensor_width = width
        self.sensor_height = height
        self.model_width = 0
        self.model_height = 0

    def process_frame(self, frame):
        for tensor in frame.tensors():
            if (self.model_width == 0):
                #generate bitmask
                
                self.model_height = tensor.dims()[1]
                self.model_width = tensor.dims()[2]
                self.ratioX = self.model_width * 1.0 / self.sensor_width
                self.ratioY = self.model_height * 1.0 / self.sensor_height
                
                for z in range(len(self.polygon)):
                    for t in range(len(self.polygon[z])>>1):
                        self.polygon[z][t<<1] = int(self.polygon[z][t<<1] * self.ratioX)
                        self.polygon[z][(t<<1)+1] = int(self.polygon[z][(t<<1)+1] * self.ratioY)

                    #convert polygon to mask algorithm
                    #https://stackoverflow.com/questions/3654289/scipy-create-2d-polygon-mask
                    self.img = Image.new('L', (self.model_width, self.model_height), 0)
                    ImageDraw.Draw(self.img).polygon(self.polygon[z], outline=1, fill=1)
                    self.mask[z] = numpy.array(self.img).flatten()
                # print("===================zone=", self.zone, "===================")
                # print("===================mask=", self.mask, "===================")
                # print("===================polygon=", self.polygon, "===================")

            else:
                #zone based crowd counting
                imgData = []
                imgData.append(tensor.data())
                
                for z in range(len(self.mask)):
                    self.crowd_count[z] = numpy.sum(self.mask[z] * imgData)
                print("===================crowd_count=", self.crowd_count, "===================")
                
        if (self.crowd_count):
            messages = list(frame.messages())
            if len(messages) > 0:
                json_msg = json.loads(messages[0].get_message())
                json_msg["count"] = {"zone"+str(self.zone[0]):int(self.crowd_count[0]), "zone"+str(self.zone[1]):int(self.crowd_count[1])}
                messages[0].set_message(json.dumps(json_msg))
                
        return True