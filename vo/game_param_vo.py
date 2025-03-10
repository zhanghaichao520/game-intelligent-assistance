class GameParamVO:
    """
    运行时的参数值
    """
    def __init__(self):
        # 当前房间在路线中的索引id
        self.map_visit = {
            (0, 0): False,
            (0, 1): False,
            (0, 2): False,
            (2, 0): False,
            (2, 1): False,
            (2, 2): False,
            (1, 0): False,
            (1, 1): False,
            (1, 2): False,
            (1, 3): False,
            (1, 4): False,
            (1, 5): False,
        }
        self.cur_route_id = 0
        # 当前房间，第几行几列
        self.cur_room = (1, 0)
        self.next_room = None
        # 是否已经刷完狮子头房间
        self.is_succ_sztroom = False
        # 随机移动时，下一个方向
        self.next_angle = 0
        # 移动超时时间
        self.move_time_out = 0

        self.mov_start = False
        # 对于只需要开启一次的技能，是否已经开启
        self.skill_start = False

        self.just_run = True