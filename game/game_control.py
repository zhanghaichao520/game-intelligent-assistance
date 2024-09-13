import random
import time
from typing import Tuple

from adb.scrcpy_adb import ScrcpyADB
import math
from vo.game_param_vo import GameParamVO


class GameControl:
    def __init__(self, adb: ScrcpyADB):
        self.adb = adb

    def calc_mov_point(self, angle: float) -> Tuple[int, int]:
        angle = angle % 360
        rx, ry = (463, 860)
        r = 140

        x = rx + r * math.cos(angle * math.pi / 180)
        y = ry - r * math.sin(angle * math.pi / 180)
        return int(x), int(y)

    def move(self, angle: float, t: float):
        # 计算轮盘x, y坐标
        x, y = self.calc_mov_point(angle)
        self.click(x, y, t)

    def stop(self):
        # 计算轮盘x, y坐标
        self.adb.touch_end(0, 0)

    def calc_move_point_direction(self, direction: str):
        if direction is None:
            return None
        # 计算轮盘x, y坐标
        angle = 0
        if direction == 'up':
            angle = 90
        if direction == 'down':
            angle = 270
        if direction == 'left':
            angle = 180
        x, y = self.calc_mov_point(angle)
        return x, y


    def attack_GQ(self, param:GameParamVO):
        """
        鬼泣逻辑
        :param index:
        :return:
        """
        if param.skill_start == False:
            print("开启BUFF")
            self.skill_3()
            param.skill_start = True

        if param.cur_room == (1,0):
            time.sleep(0.5)
            self.move(320,0.7)
            time.sleep(0.2)
            self.move(0,0.4)
            time.sleep(0.2)
            self.skill_a()
        if param.cur_room == (2,0) or param.cur_room == (0,0):
            self.move(320, 0.7)
            time.sleep(0.2)
            self.move(0, 0.15)
            for i in range(3):
                time.sleep(0.2)
                self.skill_d()
        if param.cur_room == (2,1) or param.cur_room == (0,1):
            self.move(320, 0.1)
            self.skill_up()
            time.sleep(0.1)
            self.move(0, 0.1)
        if param.cur_room == (2,2) or param.cur_room == (0,2):
            self.move(320, 0.1)
            time.sleep(0.1)
            self.skill_f()
            time.sleep(0.1)
            self.move(0, 0.1)
            self.skill_left()
            time.sleep(0.1)
            self.skill_up()
            time.sleep(0.1)
            self.continuous_attack_GQ()

        if param.cur_room == (1,2):
            self.move(90, 0.3)
            time.sleep(0.1)
            self.move(180, 0.1)
            time.sleep(0.1)
            self.skill_d()
            time.sleep(0.1)
            self.continuous_attack_GQ()

        if param.cur_room == (1,1):
            self.move(270, 0.5)
            time.sleep(0.1)
            self.move(180, 1.5)
            time.sleep(0.3)
            self.move(0, 0.1)
            for i in range(5):
                self.skill_1()
                time.sleep(0.3)
            time.sleep(0.1)
            self.continuous_attack_GQ()

        if param.cur_room == (1,3):
            self.move(320, 0.2)
            time.sleep(0.1)
            self.move(0, 0.15)
            self.skill_a()
            time.sleep(0.1)
            self.continuous_attack_GQ()

        if param.cur_room == (1,4):
            self.move(320, 0.2)
            time.sleep(0.1)
            self.move(0,0.3)
            self.skill_d()
            time.sleep(0.1)
            self.continuous_attack_GQ()

        if param.cur_room == (1,5):
            self.skill_3()
            time.sleep(0.1)
            self.move(0,0.1)
            time.sleep(0.1)
            self.skill_2()
            time.sleep(0.1)
            self.continuous_attack_GQ()


    def attack_NM(self, param:GameParamVO):
        """
        奶妈逻辑
        :param index:
        :return:
        """
        print(f"开始执行房间技能")
        if param.cur_room == (1,0):
            self.move(300,0.1)
            time.sleep(0.1)
            self.skill_4()
            time.sleep(0.1)
            self.attack(1)
        if param.cur_room == (2,0):
            self.move(270, 0.2)
            self.skill_d()
            time.sleep(0.1)
            self.skill_c()
            time.sleep(0.1)
            self.attack(1)
        if param.cur_room == (2,1):
            self.move(0, 0.1)
            time.sleep(0.1)
            self.skill_a()
            time.sleep(0.1)
            self.attack(1)
        if param.cur_room == (2,2):
            self.skill_f()
            self.skill_left()
            self.continuous_attack_GQ()
        if param.cur_room == (1,2):
            self.move(0, 0.1)
            time.sleep(0.1)
            self.skill_d()
            self.continuous_attack_GQ()
        if param.cur_room == (1,1):
            ctl.move(180, 1.5)
            time.sleep(0.3)
            ctl.move(0, 0.1)
            self.skill_1()
            self.continuous_attack_GQ()

        if param.cur_room == (1,3):
            ctl.move(0, 0.1)
            time.sleep(0.1)
            self.skill_a()
            self.continuous_attack_GQ()

        if param.cur_room == (1,4):
            self.move(0,0.3)
            self.skill_d()
            self.continuous_attack_GQ()

        if param.cur_room == (1,5):
            self.move(0,0.1)
            time.sleep(0.1)
            self.skill_2()
            self.continuous_attack_GQ()


    def continuous_attack_GQ(self):
        self.attack(1)
        self.skill_a()
        self.attack(2)
        self.skill_b()
        self.attack(1)


    def attack(self, cnt: int = 1):
        x, y = (1990, 934)
        for i in range(cnt):
            self.click(x, y)
            time.sleep(0.1)

    def skill_up(self, t: float = 0.1):
        x, y = (1850, 542)
        x, y = self._ramdon_xy(x, y)
        self.adb.slow_swipe(x, y, x, y - 100, duration=t, steps=1)

    def skill_down(self, t: float = 0.1):
        x, y = (1850, 542)
        x, y = self._ramdon_xy(x, y)
        self.adb.slow_swipe(x, y, x, y + 100, duration=t, steps=1)

    def skill_left(self, t: float = 0.1):
        x, y = (1850, 542)
        x, y = self._ramdon_xy(x, y)
        self.adb.slow_swipe(x, y, x - 100, y, duration=t, steps=1)

    def skill_right(self, t: float = 0.1):
        x, y = (1850, 542)
        x, y = self._ramdon_xy(x, y)
        self.adb.slow_swipe(x, y, x + 100, y, duration=t, steps=1)


    def click(self, x, y, t: float = 0.01):
        x, y = self._ramdon_xy(x, y)
        self.adb.touch_start(x, y)
        time.sleep(t)
        self.adb.touch_end(x, y)

    def _ramdon_xy(self, x, y):
        x = x + random.randint(-5, 5)
        y = y + random.randint(-5, 5)
        return x, y

    def skill_a(self, t: float = 0.01):
        x, y = (1552, 963)
        self.click(x, y, t)

    def skill_b(self, t: float = 0.01):
        x, y = (1720, 972)
        self.click(x, y, t)

    def skill_c(self, t: float = 0.01):
        x, y = (1750, 795)
        self.click(x, y, t)

    def skill_d(self, t: float = 0.01):
        x, y = (1864, 695)
        self.click(x, y, t)

    def skill_e(self, t: float = 0.01):
        x, y = (2025, 630)
        self.click(x, y, t)

    def skill_f(self, t: float = 0.01):
        x, y = (2040, 474)
        self.click(x, y, t)

    def skill_1(self, t: float = 0.01):
        x, y = (1750, 360)
        self.click(x, y, t)

    def skill_2(self, t: float = 0.01):
        x, y = (1840, 360)
        self.click(x, y, t)

    def skill_3(self, t: float = 0.01):
        x, y = (1945, 360)
        self.click(x, y, t)

    def skill_4(self, t: float = 0.01):
        x, y = (2044, 360)
        self.click(x, y, t)

if __name__ == '__main__':
    ctl = GameControl(ScrcpyADB(1384))


    ctl.move(180,1.5)
    time.sleep(0.3)
    ctl.move(0,0.1)



