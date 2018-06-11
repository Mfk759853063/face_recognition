# coding=utf-8
import face_recognition
import os
import time
import datetime
import multiprocessing
import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, os.path, random, string
from tornado.options import define, options
import shutil
from multiprocessing import Process, Manager

manager = Manager()
class Face(object):
    def __init__(self):
        self.authed_peoples = []
        self.unauthed_peoples = []
        self. people_labels = []
        self.unauthed_path = "./unauthed-small"
        self.authed_path = "./authed-small"
        self.cores = multiprocessing.cpu_count()
        self.pool = multiprocessing.Pool(processes=self.cores)
        self.stop = False
        self.flags = manager.dict({'find': False,"name":""})

    def __getstate__(self):
        self_dict = self.__dict__.copy()
        del self_dict['pool']
        return self_dict

    def __setstate__(self, state):
        self.__dict__.update(state)

    def load_authed_peoples(self):
        print("系统正在加载所认识的人")
        path = self.authed_path
        files = os.listdir(path)
        list = []
        for file in files:
            if not os.path.isdir(file):
                if not file.startswith("."):
                    start_time = time.time()
                    load_file = face_recognition.load_image_file(os.path.join(path, file))
                    load_file_bindry = face_recognition.face_encodings(load_file)[0]
                    end_time = time.time()
                    print("加载%s花了%.2f秒,大小是%dkb" % (file, (end_time - start_time)%60,os.path.getsize(os.path.join(path, file))/1024))
                    list.append(load_file_bindry)
        print("系统库有%d个人" % len(list))
        return list

    def load_unauthed_peoples(self):
        print("系统正在加载准备识别的人")
        path = self.unauthed_path
        files = os.listdir(path)
        list = []
        self.people_labels = []
        for file in files:
            if not os.path.isdir(file):
                if not file.startswith("."):
                    self.people_labels.append(os.path.splitext(file)[0])
                    start_time = time.time()
                    load_file = face_recognition.load_image_file(os.path.join(path, file))
                    load_file_bindry = face_recognition.face_encodings(load_file)[0]
                    end_time = time.time()
                    print("加载%s花了%.2f秒,大小是%dkb" % (file, (end_time - start_time)%60,os.path.getsize(os.path.join(path, file))/1024))
                    list.append(load_file_bindry)
                    
        print("准备识别的人有%d个" % len(list))
        return list
    
    def start_recognition(self,index):
        if self.flags["find"] is True:
            return
        start_time = time.time()
        results = face_recognition.compare_faces(self.authed_peoples,self.unauthed_peoples[index])
        end_time = time.time()
        if results[0] == 1:
            self.flags["find"] = True
            self.flags["name"] = self.people_labels[index]
            print("系统识别到此人,%s花了%f秒，当前worker名字%s" % (self.people_labels[index],(end_time - start_time)%60,multiprocessing.current_process().name))
        else:
            print("系统未识别到,%s花了%f秒，当前worker名字%s" % (self.people_labels[index], (end_time - start_time) % 60, multiprocessing.current_process().name))

    def setup(self):
        print("加载中...")
        self.authed_peoples = self.load_authed_peoples()

    def startRandromTest(self):
        print("开始随机测试，当前系统加载cpu{}个...".format(self.cores))
        k = 0
        while not self.stop:
            if k >= 1:
                self.stop = True
                continue
            k = k+1
            for i in range(2):
                print("*******************開始第%d次测试******************" % (i+1))
                start_time = time.time()
                self.start()
                end_time = time.time()
                print("*******************第%d次测试完成,识别共花了%.2f秒******************" % (i+1,(end_time-start_time)%60))
        
    def start(self):
        self.unauthed_peoples = self.load_unauthed_peoples()
        self.pool.map(self.start_recognition, range(len(self.unauthed_peoples)))
        self.pool.close()
        self.pool.join()
        self.pool = multiprocessing.Pool(processes=self.cores)
        print("退出...")
        find = self.flags["find"]
        name = self.flags["name"]
        self.flags["find"] = False
        self.flags["name"] = ""
        return (find,name)


class FaceHandler(tornado.web.RequestHandler):
    def post(self):
        new_path = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
        new_path = "static/uploads/" + new_path
        os.makedirs(new_path);
        for file_name in self.request.files.keys():
            file = self.request.files[file_name][0]
            original_fname = file['filename']
            final_filename = original_fname
            output_file = open(new_path+"/" + final_filename, 'wb+')
            output_file.write(file['body'])
            output_file.close()
        face.unauthed_path = new_path
        result,name = face.start()
        if result:
            self.finish("找到此人%s" % name)
        else:
            self.finish("未找到此人")


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/api/faceRecognition", FaceHandler)
        ]
        tornado.web.Application.__init__(self, handlers)

define("port", default=9999, help="run on the given port", type=int)

def start_recognition_server():
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    face = Face()
    face.setup()
    # face.unauthed_path = "static/uploads"
    # result, name = face.start()
    # if result:
    #     print("找到此人%s" % name)
    # else:
    #     print("未找到此人")

    start_recognition_server()

    
    
    


