"""
Author: wind windzu1@gmail.com
Date: 2023-08-29 12:04:30
LastEditors: wind windzu1@gmail.com
LastEditTime: 2023-08-29 12:04:38
Description: 
Copyright (c) 2023 by windzu, All Rights Reserved. 
"""
"""
Author: wind windzu1@gmail.com
Date: 2023-08-27 18:34:41
LastEditors: wind windzu1@gmail.com
LastEditTime: 2023-08-28 00:09:36
Description: 
Copyright (c) 2023 by windzu, All Rights Reserved. 
"""
import os

import cv2
import numpy as np
import yaml

from .utils import euler_to_rotation_matrix


class TopicInfo:
    def __init__(self, topic, sensor_type, msg_type):
        self.topic = topic
        self.sensor_type = sensor_type  # lidar, camera, radar
        self.msg_type = msg_type

    def __repr__(self):
        return f"TopicInfo(topic={self.topic}, sensor_type={self.sensor_type}, msg_type={self.msg_type})"


class CalibInfo:
    def __init__(self, frame_id, config):
        self.frame_id = frame_id
        self.config = config
        self.transform_matrix = self.get_transform_matrix(config["tf_config"])

    def get_transform_matrix(self, tf_config):
        """获取transform matrix
        Returns:
            np.ndarray: 4x4的transform matrix
        """
        transform = np.eye(4)
        # rotation
        tf_x = tf_config["tf_x"]
        tf_y = tf_config["tf_y"]
        tf_z = tf_config["tf_z"]
        tf_roll = tf_config["tf_roll"]
        tf_pitch = tf_config["tf_pitch"]
        tf_yaw = tf_config["tf_yaw"]

        # r = R.from_euler("xyz", [tf_roll, tf_pitch, tf_yaw], degrees=True)
        # rotation = r.as_matrix()
        rotation = euler_to_rotation_matrix(tf_roll, tf_pitch, tf_yaw)
        # translation
        translation = np.array([tf_x, tf_y, tf_z]).reshape(3, 1)
        transform[:3, :3] = rotation
        transform[:3, 3] = translation.flatten()

        formatted_transform = np.array(
            [[format(val, ".6f") for val in row] for row in transform], dtype=float
        )

        return formatted_transform

    def __repr__(self):
        return f"CalibInfo(frame_id={self.frame_id}, transform_matrix={self.transform_matrix})"


# 读取配置文件
def read_config(path="./config.yaml"):
    with open(path, "r") as file:
        config = yaml.safe_load(file)
    return config


def parse_config(path="./config.yaml"):
    # 获取进程数
    worker_num = parse_worker_num(path)
    # 获取所有需要解压的文件
    compressed_files = parse_compressed_file_list(path)
    # 获取所有需要解析的文件
    files = parse_file_list(path)
    # 获取数据集根路径
    dataset_root = parse_dataset_root(path)
    # 获取保存的根路径
    save_root = parse_save_root(path)
    # 获取所有需要解析的topic
    topics = parse_topic_list(path)
    topic_info_list = parse_topic_infos(path)
    # 获取topics alias
    topics_alias_dict = parse_topics_alias(path)
    # 获取主topic
    main_topic = parse_main_topic(path)

    # 获取时间戳阈值(ms)
    time_diff_threshold = parse_time_diff_threshold(path)
    # 获取采样间隔(frame)
    sample_interval = parse_sample_interval(path)
    # 获取是否保存sweep数据
    save_sweep_data = parse_save_sweep_data(path)

    # 获取标定信息
    cars_calib_info_dict = parse_calib(path)

    return {
        "worker_num": worker_num,
        "compressed_files": compressed_files,
        "files": files,
        "dataset_root": dataset_root,
        "save_root": save_root,
        "topics": topics,
        "topic_info_list": topic_info_list,
        "topics_alias_dict": topics_alias_dict,
        "main_topic": main_topic,
        "time_diff_threshold": time_diff_threshold,
        "sample_interval": sample_interval,
        "save_sweep_data": save_sweep_data,
        "cars_calib_info_dict": cars_calib_info_dict,
    }


# 读取进程数
def parse_worker_num(path="./config.yaml"):
    config = read_config(path)

    # 获取配置值
    worker_num = config["worker_num"]
    return worker_num


# 读取压缩文件列表
def parse_compressed_file_list(path="./config.yaml"):
    config = read_config(path)

    # 获取配置值
    dataset_root = config["dataset_root"]
    exclude_path = config["exclude_path"]
    suffix = config["compressed_data_suffix"]

    def get_files_from_directory(directory, suffix, excluded_paths):
        file_list = []

        # 遍历指定目录
        for dirpath, dirnames, filenames in os.walk(directory):
            # 检查当前目录是否在排除列表中
            if not any(dirpath.startswith(ex_path) for ex_path in excluded_paths):
                for filename in filenames:
                    if filename.endswith(suffix):
                        file_list.append(os.path.join(dirpath, filename))
        return file_list

    files = get_files_from_directory(dataset_root, suffix, exclude_path)

    # 判断是否已经解压
    def is_uncompressed(file):
        uncompressed_file = file.rstrip(suffix)  # 去除压缩后缀，您可能需要根据实际情况调整这一部分
        return os.path.exists(uncompressed_file)

    # 过滤已解压的文件
    files = list(filter(lambda x: not is_uncompressed(x), files))

    return files


# 读取文件列表
def parse_file_list(path="./config.yaml"):
    config = read_config(path)

    # 获取配置值
    dataset_root = config["dataset_root"]
    exclude_path = config["exclude_path"]
    suffix = config["data_suffix"]

    def get_files_from_directory(directory, suffix, excluded_paths):
        file_list = []

        # 遍历指定目录
        for dirpath, dirnames, filenames in os.walk(directory):
            # 检查当前目录是否在排除列表中
            if dirpath not in excluded_paths:
                for filename in filenames:
                    if filename.endswith(suffix):
                        file_list.append(os.path.join(dirpath, filename))
        return file_list

    files = get_files_from_directory(dataset_root, suffix, exclude_path)
    return files


# 读取数据根路径
def parse_dataset_root(path="./config.yaml"):
    config = read_config(path)

    # 获取配置中的topics
    dataset_root = config["dataset_root"]
    return dataset_root


# 读取保存根路径
def parse_save_root(path="./config.yaml"):
    config = read_config(path)

    # 获取配置中的topics
    save_root = config["save_root"]
    return save_root


# 读取topic列表
def parse_topic_list(path="./config.yaml"):
    config = read_config(path)

    # 获取配置中的topics
    topic_data = config["topics"]

    def extract_topics(data):
        topics = []
        if isinstance(data, dict):
            for key, value in data.items():
                if value:
                    topics.extend(extract_topics(value))
                else:
                    topics.append(key)
        elif isinstance(data, list):
            for item in data:
                topics.extend(extract_topics(item))
        else:
            topics.append(data)
        return topics

    topics = extract_topics(topic_data)
    return topics


def parse_topic_infos(path="./config.yaml"):
    config = read_config(path)

    topic_data = config["topics"]
    msg_type_data = config["msg_type"]

    topic_infos = []

    def extract_topics(data, sensor_type):
        topics = []
        if isinstance(data, dict):
            for key, value in data.items():
                if value:
                    # 如果值不为空（例如，lidar），则递归提取
                    topics.extend(extract_topics(value, key))
                else:
                    # 否则，这是一个主题名，创建TopicInfo对象
                    topics.append(
                        TopicInfo(
                            topic=key,
                            sensor_type=sensor_type,
                            msg_type=msg_type_data[key],
                        )
                    )
        elif isinstance(data, list):
            for item in data:
                # 如果值是列表，为列表中的每个主题创建TopicInfo对象
                topics.append(
                    TopicInfo(
                        topic=item,
                        sensor_type=sensor_type,
                        msg_type=msg_type_data[sensor_type],
                    )
                )
        else:
            # 否则，这是一个主题名，创建TopicInfo对象
            topics.append(
                TopicInfo(
                    topic=data,
                    sensor_type=sensor_type,
                    msg_type=msg_type_data[sensor_type],
                )
            )
        return topics

    topic_infos = extract_topics(topic_data, None)
    return topic_infos


# 读取 topic 的别名
def parse_topics_alias(path="./config.yaml"):
    config = read_config(path)

    # 获取配置中的topics
    topics_alias_dict = config["topics_alias"]
    return topics_alias_dict


# 读取主topic
def parse_main_topic(path):
    config = read_config(path)

    # 获取配置中的topics
    main_topic = config["main_topic"]
    return main_topic


# 读取采样间隔
def parse_sample_interval(path):
    config = read_config(path)

    # 获取配置中的topics
    sample_interval = config["sample_interval"]
    return sample_interval


# 读取是否保存sweep数据
def parse_save_sweep_data(path):
    config = read_config(path)

    # 获取配置中的topics
    save_sweep_data = config["save_sweep_data"]
    return save_sweep_data


# 读取标定信息
def parse_calib(path="./config.yaml"):
    topics_alias_dict = parse_topics_alias(path)

    config = read_config(path)

    # 获取配置中的topics
    calib = config["calib"]
    load_way = calib["load_way"]
    cars_calib_info_dict = {}
    if load_way == "offline":
        print("will load calib from offline file")
        calib_path = calib["calib_path"]
        # check path
        if not os.path.exists(calib_path):
            print("calib path not exist")
            return None
        # 便利该文件夹下所有yaml文件
        calib_files = []
        for dirpath, dirnames, filenames in os.walk(calib_path):
            for filename in filenames:
                if filename.endswith(".yaml"):
                    calib_files.append(os.path.join(dirpath, filename))

        for calib_file in calib_files:
            car_name = os.path.basename(calib_file).split(".")[0]
            with open(calib_file, "r") as file:
                calib_data = yaml.safe_load(file)
                calib_info_dict = {}
                for key, value in calib_data.items():
                    frame_id = topics_alias_dict[key]
                    calib_info = CalibInfo(frame_id=frame_id, config=value)
                    calib_info_dict[frame_id] = calib_info
                cars_calib_info_dict[car_name] = calib_info_dict
    else:
        print("will load calib from config")
        calib_path = None
        calib = None
        cars_calib_info_dict = {}
    return cars_calib_info_dict


# 读取时间戳阈值
def parse_time_diff_threshold(path):
    config = read_config(path)

    # 获取配置中的topics
    time_diff_threshold = config["time_diff_threshold"]
    return time_diff_threshold


def parse_topic(path="./config.yaml"):
    """从config文件中解析rostopic
    Args:
        path (str, optional): 配置文件路径. Defaults to "./config.yaml".
    Returns:
        dict: 目标的topic和对应的消息类型字典
    """
    # judge file exist
    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        config = yaml.safe_load(f)
    if "topic" not in config:
        print("topic not in config")
        return None

    topic_dict = config["topic"]
    return topic_dict