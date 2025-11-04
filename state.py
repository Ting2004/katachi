import time
import json


attributes = [
    'health',
    'hydration',
    'sleep',
    'energy',
    'relax',
    'focus',
    'mood',
    'social'
]

class State:

    # initialization
    def __init__(self, filename, init_metrics, decay_rates=None):
        """
        filename: 存档文件
        init_metrics: 初始属性字典
        decay_rates: 每小时衰减量字典，例如 {'energy': -1, 'focus': -0.5}
        """
        self.filename = filename
        self.metrics = init_metrics
        self.last_update = time.time()  # 上次更新时间
        self.decay_rates = decay_rates or {}  # 默认空字典
        self.load_state()
    

    # ---------- Getter / Setter ----------
    def get_state(self):
        return self.metrics

    def get_metric(self, key):
        return self.metrics.get(key, None)

    def update_metric(self, key, value):
        if key in self.metrics:
            self.metrics[key] = max(0, min(100, self.metrics[key] + value))

    def set_metric(self, key, value):
        if key in self.metrics:
            self.metrics[key] = max(0, min(100, value))

    # ---------- Decay ----------
    def apply_decay(self):
        """根据时间差应用衰减"""
        now = time.time()
        elapsed_hours = (now - getattr(self, 'last_update', now)) / 3600  # 秒转小时

        for key, rate in self.decay_rates.items():
            if key in self.metrics:
                self.metrics[key] = max(0, min(100, self.metrics[key] + rate * elapsed_hours))

        self.last_update = now

    # ---------- IO ----------
    def save_state(self):
        data = {
            'metrics': self.metrics,
            'last_update': self.last_update
        }
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_state(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.metrics.update(data.get('metrics', {}))
                self.last_update = data.get('last_update', time.time())
        except FileNotFoundError:
            self.save_state()
