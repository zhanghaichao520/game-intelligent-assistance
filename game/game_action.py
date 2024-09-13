import random
import traceback
from typing import Tuple

from utils import room_calutil
from utils.cvmatch import image_match_util
from utils.yolov5 import YoloV5s
from game.game_control import GameControl
from adb.scrcpy_adb import ScrcpyADB
import time
import cv2 as cv
from ncnn.utils.objects import Detect_Object
import math
import numpy as np

from vo.game_param_vo import GameParamVO


def get_detect_obj_bottom(obj: Detect_Object) -> Tuple[int, int]:
    """
        计算检测对象的底部中心坐标。

        该函数通过给定的检测对象，计算其矩形区域的底部中心坐标。
        这对于需要对对象进行底部对齐或基于底部进行定位的算法非常有用。

        参数:
        obj: Detect_Object 类型的实例，表示一个检测到的对象，具有矩形属性 rect。

        返回值:
        一个元组 (x, y)，其中 x 是底部中心的横坐标，y 是底部中心的纵坐标。
    """
    return int(obj.rect.x + obj.rect.w / 2), int(obj.rect.y + obj.rect.h)


def get_detect_obj_right(obj: Detect_Object) -> Tuple[int, int]:
    return int(obj.rect.x + obj.rect.w), int(obj.rect.y + obj.rect.h/2)


def get_detect_obj_center(obj: Detect_Object) -> Tuple[int, int]:
    return int(obj.rect.x + obj.rect.w/2), int(obj.rect.y + obj.rect.h/2)


def distance_detect_object(a: Detect_Object, b: Detect_Object):
    """
       计算两个检测对象之间的欧几里得距离。

       参数:
       a: Detect_Object 类型的实例，表示第一个检测对象。
       b: Detect_Object 类型的实例，表示第二个检测对象。

       返回值:
       返回两个检测对象之间的距离，距离值为浮点数。
    """
    return math.sqrt((a.rect.x - b.rect.x) ** 2 + (a.rect.y - b.rect.y) ** 2)


def calc_angle(x1, y1, x2, y2):
    """
        计算两个点之间的角度。

        该函数通过计算两个点(x1, y1)和(x2, y2)构成的向量与x轴的夹角，返回该夹角的度数。
        返回的角度在0到180度之间。

        参数:
        x1 (float): 第一个点的x坐标。
        y1 (float): 第一个点的y坐标。
        x2 (float): 第二个点的x坐标。
        y2 (float): 第二个点的y坐标。

        返回:
        int: 两个点之间的角度，以度为单位。
    """
    angle = math.atan2(y1 - y2, x1 - x2)
    return 180 - int(angle * 180 / math.pi)


class GameAction:

    def __init__(self, ctrl: GameControl):
        self.ctrl = ctrl
        self.yolo = YoloV5s(target_size=640,
                            prob_threshold=0.25,
                            nms_threshold=0.45,
                            num_threads=4,
                            use_gpu=True)
        self.adb = self.ctrl.adb
        self.param = GameParamVO()

    def find_result(self):
        while True:
            time.sleep(0.01)
            screen = self.ctrl.adb.last_screen
            if screen is None:
                continue
            result = self.yolo(screen)
            self.display_image(screen, result)
            return screen, result

    def display_image(self, screen, result):
        if screen is None:
            return
        for obj in result:
            color = (2 ** (obj.label % 9) - 1, 2 ** ((obj.label + 4) % 9) - 1, 2 ** ((obj.label + 8) % 9) - 1)

            cv.rectangle(screen,
                         (int(obj.rect.x), int(obj.rect.y)),
                         (int(obj.rect.x + obj.rect.w), int(obj.rect.y + + obj.rect.h)),
                         color, 2
                         )
            text = f"{self.yolo.class_names[int(obj.label)]}:{obj.prob:.2f}"
            self.adb.plot_one_box([obj.rect.x, obj.rect.y, obj.rect.x + obj.rect.w, obj.rect.y + obj.rect.h], screen,
                                  color=color, label=text, line_thickness=2)
        cv.imshow('screen', screen)
        cv.waitKey(1)

    def get_cur_room_index(self):
        """
        获取当前房间的索引，需要看地图
        :return:
        """
        route_map = None
        result = None
        fail_cnt = 0
        while True:
            self.ctrl.click(2105, 128)
            time.sleep(0.3)
            screen = self.ctrl.adb.last_screen
            if screen is None:
                continue
            start_time = time.time()
            result = self.yolo(screen)
            self.display_image(screen, result)
            route_map = self.find_one_tag(result, 'map')
            if route_map is not None:
                break
            else:
                fail_cnt += 1
                time.sleep(0.05)
                if fail_cnt > 8:
                    print('*******************************地图识别失败*******************************')
                    return None, None, None

        if route_map is not None:
            # 关闭地图
            tmp = self.find_one_tag(self.yolo(self.ctrl.adb.last_screen), 'map')
            if tmp is not None:
                self.ctrl.click(2105, 128)
            point = self.find_one_tag(result, 'point')
            if point is None:
                return 9, (1,5), None
            # 转换成中心点的坐标
            point = get_detect_obj_center(point)
            route_id, cur_room = room_calutil.get_cur_room_index(point)
            return route_id, cur_room, point

        return None, None, None

    def move_to_next_room(self):
        """
        过图
        :return:
        """
        move_door_cnt = 0
        hero_no = 0
        if self.param.cur_room == (1, 5):
            return
        while True:
            move_door_cnt += 1
            screen, result = self.find_result()
            # 2 判断是否过图成功
            ada_image = cv.adaptiveThreshold(cv.cvtColor(screen, cv.COLOR_BGR2GRAY), 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 13, 3)
            if np.sum(ada_image) <= 10000000:
                print(f'*******************************过图成功, 当前房间 {self.param.cur_room}*******************************')
                self.param.mov_start = False
                self.adb.touch_end(0, 0)
                self.param.route_id, self.param.cur_room, point = self.get_cur_room_index()
                return
            # 如果有怪物和装备，就停止过图
            if len(self.find_tag(result, ['Monster_szt', 'Monster_ds', 'Monster', 'equipment'])) > 0:
                print('有怪物或装备，停止过图')
                self.param.mov_start = False
                self.adb.touch_end(0, 0)
                return


            if self.param.cur_room == (1,1):
                self.param.is_succ_sztroom = True


            # 3 先找到英雄位置，在找到对应方向的门进入
            hero = self.find_one_tag(result, 'hero')
            if hero is None:
                hero_no += 1
                if hero_no > 5:
                    hero_no = 0
                    self.no_hero_handle(result)
                continue

            hero = hero[0]
            hx, hy = get_detect_obj_bottom(hero)

            arrow = self.find_tag(result, ['go', 'go_d', 'go_r', 'go_u', 'go_l'])

            door = self.find_tag(result, ['opendoor_d', 'opendoor_r', 'opendoor_u', 'opendoor_l'])

            count = 3
            for i in range(count):
                time.sleep(0.25)
                if len(arrow) > 0:
                    self.move_to_target(arrow, hero, hx, hy, screen)
                if i == count - 1:
                    return
            # if len(door) != 0:
            #     select_d = None
            #     #第1个房间找最下面的门，
            #     if self.param.cur_room == (1, 0):
            #         for d in door:
            #             if d.label == 11:
            #                 select_d = d
            #
            #     # 第2个房间找最右面的门，
            #     if self.param.cur_room == (2, 0) or self.param.cur_room == (2, 1) or self.param.cur_room == (1, 3) or self.param.cur_room == (1, 4):
            #         for d in door:
            #             if d.label == 13:
            #                 select_d = d
            #
            #     # 第4个房间找最上面的门，
            #     if self.param.cur_room == (2, 2):
            #         for d in door:
            #             if d.label == 14:
            #                 select_d = d
            #
            #     # 第5个房间
            #     if self.param.cur_room == (1, 2) and not self.param.is_succ_sztroom:
            #         self.ctrl.move(150,0.5)
            #         for d in door:
            #             if d.label == 12:
            #                 select_d = d
            #     # 第5个房间
            #     if self.param.cur_room == (1, 2) and self.param.is_succ_sztroom:
            #         self.ctrl.move(0, 0.5)
            #         for d in door:
            #             if d.label == 13:
            #                 select_d = d
            #
            #     if self.param.cur_room == (1, 2):
            #         for d in door:
            #             if d.label == 11:
            #                 dis = distance_detect_object(hero, d)
            #                 if dis < 30:
            #                     self.ctrl.move(90, 0.2)
            #             if d.label == 14:
            #                 dis = distance_detect_object(hero, d)
            #                 if dis < 30:
            #                     self.ctrl.move(270, 0.2)
            #             if d.label == 12:
            #                 dis = distance_detect_object(hero, d)
            #                 if dis < 30:
            #                     self.ctrl.move(90, 0.2)
            #     if select_d is None:
            #         self.no_hero_handle(is_attack=False)
            #         continue
            #     ax, ay = get_detect_obj_bottom(select_d)
            #
            # if len(arrow) != 0 and not self.param.cur_room == (1, 2):
            #     min_distance_arrow = min(arrow, key=lambda a: distance_detect_object(hero, a))
            #     ax, ay = get_detect_obj_bottom(min_distance_arrow)
            #
            #
            # cv.circle(screen, (hx, hy), 5, (0, 255, 0), 5)
            # cv.arrowedLine(screen, (hx, hy), (ax, ay), (255, 0, 0), 3)
            # angle = calc_angle(hx, hy, ax, ay)
            # step_time = 0.3
            # self.ctrl.move(angle, step_time)

            if move_door_cnt > 20:
                move_door_cnt = 0
                print('***************过门次数超过20次，随机移动一下*******************************')
                self.no_hero_handle(is_attack=False)



    def move_to_target(self, target: list, hero, hx, hy, screen):
        min_distance_obj = min(target, key=lambda a: distance_detect_object(hero, a))
        ax, ay = get_detect_obj_bottom(min_distance_obj)
        if self.yolo.class_names[int(min_distance_obj.label)] == 'opendoor_l':
            ax, ay = get_detect_obj_right(min_distance_obj)
        # 装备标了名称，所以要加40，实际上在下方
        if self.yolo.class_names[int(min_distance_obj.label)] == 'equipment':
            ay += 60
        self.craw_line(hx, hy, ax, ay, screen)

        angle = calc_angle(hx, hy, ax, ay)
        # 根据角度计算移动的点击点
        self.ctrl.move(angle, 0.2)


    def no_hero_handle(self,is_attack = True):
        """
        找不到英雄或卡墙了，随机移动，攻击几下
        :param result:
        :param t:
        :return:
        """
        for i in range(2):
            angle = random.randrange(start=0, stop=360)
            # print(f'正在随机移动。。。随机角度移动{angle}度。')
            self.ctrl.move(angle, 0.3)
            time.sleep(0.2)
            if is_attack:
                self.ctrl.attack(1)
                time.sleep(0.2)

    def move_to_xy(self, x, y, out_time=2):
        """
        移动到指定位置,默认2秒超时
        :param x:
        :param y:
        :return:
        """
        if (time.time() - self.param.move_time_out) >= out_time:
            self.param.move_time_out = time.time()
            self.param.mov_start = False

        if not self.param.mov_start:
            self.adb.touch_end(x, y)
            self.adb.touch_start(x, y)
            self.param.mov_start = True
            self.adb.touch_move(x-1, y)
        else:
            self.adb.touch_move(x, y)

    def pick_up_equipment(self):
        """
        捡装备
        :return:
        """
        hero_no = 0
        while True:
            screen, result = self.find_result()

            hero = self.find_tag(result, 'hero')
            if len(hero) == 0:
                hero_no += 1
                if hero_no > 5:
                    hero_no = 0
                    self.no_hero_handle(result)
                continue

            monster = self.find_tag(result, ['Monster', 'Monster_ds', 'Monster_szt','card'])
            if len(monster) > 0:
                print('找到怪物，或者发现卡片，停止捡装备。。')
                return

            hero = hero[0]
            hx, hy = get_detect_obj_bottom(hero)

            equipment = self.find_tag(result, 'equipment')

            count = 3
            for i in range(count):
                time.sleep(0.25)
                if len(equipment) > 0:
                    self.move_to_target(equipment, hero, hx, hy, screen)
                if i == count - 1:
                    return

    def attack_master(self):
        """
        找到怪物，攻击怪物
        :return:
        """
        attak_cnt = 0
        check_cnt = 0
        print(f'开始攻击怪物,当前房间：{self.param.cur_route_id}')
        while True:
            # 找地图上包含的元素
            screen, result = self.find_result()
            card = self.find_tag(result, ['card'])
            if len(card) > 0:
                print('找到翻牌的卡片，不攻击')
                return

            hero = self.find_tag(result, 'hero')
            if len(hero) == 0:
                self.no_hero_handle(result)
                continue

            hero = hero[0]
            hx, hy = get_detect_obj_bottom(hero)
            cv.circle(screen, (hx, hy), 5, (0, 0, 125), 5)
            monster = self.find_tag(result, ['Monster', 'Monster_ds', 'Monster_szt'])
            if len(monster) > 0:
                print('怪物数量：', len(monster))

                # 最近距离的怪物坐标
                nearest_monster = min(monster, key=lambda a: distance_detect_object(hero, a))
                distance = distance_detect_object(hero, nearest_monster)
                ax, ay = get_detect_obj_bottom(nearest_monster)
                # 判断在一条直线上再攻击
                y_dis = abs(ay - hy)
                # print(f'最近距离的怪物坐标：{ax},{ay},距离：{distance},y距离：{y_dis}')

                if distance <= 600 * room_calutil.zoom_ratio and y_dis <= 100*room_calutil.zoom_ratio:
                    self.adb.touch_end(ax, ay)
                    self.param.mov_start = False
                    # 面向敌人
                    angle = calc_angle(hx, hy, ax, hy)
                    self.ctrl.move(angle, 0.2)
                    print(f'====================敌人与我的角度{angle}==攻击怪物，攻击次数：{attak_cnt},{self.param.cur_room}')
                    attak_cnt += 1
                    self.ctrl.attack()
                    time.sleep(0.1)
                    self.ctrl.continuous_attack_GQ()

                # 怪物在右边,就走到怪物走边400的距离
                if ax > hx:
                    ax = int(ax - 500 * room_calutil.zoom_ratio)
                else:
                    ax = int(ax + 500 * room_calutil.zoom_ratio)
                self.craw_line(hx, hy, ax, ay, screen)
                angle = calc_angle(hx, hy, ax, ay)
                self.ctrl.move(angle, 0.2)
            else:
                check_cnt += 1
                if check_cnt >= 5:
                    return


    def craw_line(self, hx, hy, ax, ay, screen):
        # cv.circle(screen, (hx, hy), 5, (0, 0, 125), 5)
        # 计算需要移动到的的坐标
        cv.circle(screen, (hx, hy), 5, (0, 255, 0), 5)
        cv.circle(screen, (ax, ay), 5, (0, 255, 255), 5)
        cv.arrowedLine(screen, (hx, hy), (ax, ay), (255, 0, 0), 3)
        cv.imshow('screen', screen)
        cv.waitKey(1)


    def find_tag(self, result, tag):
        """
        根据标签名称来找到目标
        :param result:
        :param tag:
        :return:
        """
        item = [x for x in result if self.yolo.class_names[int(x.label)] in tag]
        return item

    def find_one_tag(self,result,tag):
        """
        根据标签名称来找到目标
        :param result:
        :param tag:
        :return:
        """
        reslist = [x for x in result if self.yolo.class_names[int(x.label)] == tag]
        if len(reslist) == 0:
            print(f'没有找到标签{tag}')
            return None
        else:
            return reslist[0]

    def reset_start_game(self):
        """
        重置游戏，回到初始状态
        :return:
        """
        time.sleep(3)
        for i in range(3):
            time.sleep(0.5)
            self.ctrl.click(2050,130)
        # 出现卡片，就是打完了，初始化数值
        self.param = GameParamVO()


def run():
    ctrl = GameControl(ScrcpyADB(1384))
    action = GameAction(ctrl)


    while True:
        try:
            # 启动定位当前房间
            if action.param.just_run:
                action.param.route_id, action.param.cur_room, point = action.get_cur_room_index()
                if action.param.cur_room is not None:
                    action.param.just_run = False
                    print(f"首次启动， 定位当前房间为 {action.param.cur_route_id} 号")

            screen, result = action.find_result()

            if not action.param.map_visit[action.param.cur_room]:
                print(f"首次进入房间 {action.param.cur_room}")
                action.param.map_visit[action.param.cur_room] = True
                action.ctrl.attack_GQ(action.param)

            # 根据出现的元素分配动作
            for i in range(2):
                if len(action.find_tag(result, 'equipment')) > 0:
                    print('--------------------------------发现装备，开始捡起装备--------------------------------')
                    action.pick_up_equipment()
                    action.ctrl.stop()
                else:
                    action.no_hero_handle(is_attack=False)

            if len(action.find_tag(result, ['Monster', 'Monster_ds', 'Monster_szt'])) > 0:
                print('--------------------------------发现怪物，开始攻击--------------------------------')
                action.attack_master()
                action.ctrl.stop()

            if len(action.find_tag(result, ['go', 'go_d', 'go_r', 'go_u','opendoor_d', 'opendoor_r', 'opendoor_u', 'opendoor_l'])) > 0:
                print('--------------------------------发现门，开始移动到下一个房间--------------------------------')
                action.move_to_next_room()
                action.param.mov_start = False

            if len(action.find_tag(result, 'card')) > 0:
                print('打完了，去翻牌子')
                time.sleep(1)
                action.ctrl.adb.tap(2060, 475)
                time.sleep(0.1)
                action.ctrl.adb.tap(2060, 475)

                if action.param.cur_room == (1, 5):
                    for i in range(3):
                        if len(action.find_tag(result, 'equipment')) > 0:
                            print('--------------------------------发现装备，开始捡起装备--------------------------------')
                            action.pick_up_equipment()
                            action.ctrl.stop()
                        else:
                            action.no_hero_handle()
                    action.reset_start_game()

        except Exception as e:
            action.param.mov_start = False
            print(f'出现异常:{e}')
            traceback.print_exc()

    print('程序结束...')
    while True:
        print('全部完成，展示帧画面...')
        time.sleep(0.1)



if __name__ == '__main__':
    # 程序入口
    run()
