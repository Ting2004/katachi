from objects.state import attributes
from datetime import datetime, timedelta

def check_valid_effect(effect):
    for key in effect.keys():
        if key not in attributes:
            return False
    return True


class Task:
    
    def __init__(self, name, effect, task_type, label=None):
        if not check_valid_effect(effect):
            raise ValueError("Invalid effect keys.")
        self.name = name
        self.effect = effect
        self.type = task_type
        self.label = label

    def get_info(self):
        return {'name': self.name, 'effect': self.effect, 'type': self.type, 'label': self.label}
    def get_name(self):
        return self.name
    def get_effect(self):
        return self.effect
    def get_type(self):
        return self.type
    def get_label(self):
        return self.label
    def set_effect(self, new_effect):
        if not check_valid_effect(new_effect):
            raise ValueError("Invalid effect keys.")
        self.effect = new_effect
    def set_name(self, new_name):
        self.name = new_name
    def set_type(self, new_type):
        self.type = new_type
    def set_label(self, new_label):
        self.label = new_label

    

class TaskList:
    def __init__(self, filename):
        self.all_tasks = dict()
        self.filename = filename
        self.last_reset_time = datetime.now().date()
        self.load_tasks()

    def reset_completion_status(self, manual_reset=False):
        """检查是否跨过上次的凌晨4点，如果是则重置所有任务状态"""
        now = datetime.now()
        last_reset_point = datetime.combine(self.last_reset_time, datetime.min.time()) + timedelta(hours=4)

        # 如果已经跨过新的4点
        if now >= last_reset_point + timedelta(days=1) or manual_reset:
            print(f"重置任务完成状态")
            for task_entry in self.all_tasks.values():
                if task_entry is not None:
                    task_entry['completed'] = False
                    task_entry['count'] = 0
            self.last_reset_time = now.date()
            self.save_tasks()
        
    def reset_entries(self, new_tasks):
        self.all_tasks = dict()
        for key, task_dict in new_tasks.items():
            task_obj = Task(task_dict['name'], task_dict['effect'], task_dict['type'], task_dict.get('label', None))
            self.all_tasks[task_dict['name']] = {
                'task': task_obj,
                'completed': task_dict['completed'],
                'count': task_dict['count']
            }
    




    def list_all(self):
        return list(self.all_tasks.values())
    
    def save_tasks(self):
        import json
        tasks_data = {}
        for task_name, task_entry in self.all_tasks.items():
            if task_entry is not None:
                task_obj = task_entry.get('task')
                tasks_data[task_name] = {
                    'name': task_obj.name,
                    'effect': task_obj.effect,
                    'type': task_obj.type,
                    'label': task_obj.label,
                    'completed': task_entry.get('completed', False),
                    'count': task_entry.get('count', 0)
                }
        with open('tasks.json', 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

    def load_tasks(self):
        import json
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
                for task_name, task_info in tasks_data.items():
                    task_obj = Task(task_info['name'], task_info['effect'], task_info['type'], task_info['label'])
                    self.all_tasks[task_name] = {
                        'task': task_obj,
                        'completed': task_info.get('completed', False),
                        'count': task_info.get('count', 0)
                    }
        except FileNotFoundError:
            self.save_tasks()


    def complete_task(self, task_name):
        task_entry = self.get_task(task_name)
        if task_entry:
            task = task_entry['task']
            if task.get_type() == 'check':
                task_entry['completed'] = True
            elif task.get_type() == 'counter':
                task_entry['count'] += 1
            print(f"Task '{task_name}' marked as completed.")
            return True
        else:
            print(f"Task '{task_name}' not found.")
            return False
    
    def uncomplete_task(self, task_name):
        task_entry = self.get_task(task_name)
        if task_entry:
            task = task_entry['task']
            if task.get_type() == 'check':
                task_entry['completed'] = False
            elif task.get_type() == 'counter' and task_entry['count'] > 0:
                task_entry['count'] -= 1
            print(f"Task '{task_name}' marked as uncompleted.")
            return True
        else:
            print(f"Task '{task_name}' not found.")
            return False
        
    def toggle_task_type(self, task_name):
        task_entry = self.get_task(task_name)
        if task_entry:
            task = task_entry['task']
            if task.get_type() == 'check':
                task.set_type('counter')
                task_entry['count'] = 0 if not task.get('completed') else 1
            elif task.get_type() == 'counter':
                task.set_type('check')
                task_entry['completed'] = False if task.get('count', 0) == 0 else True
            print(f"Task '{task_name}' type toggled.")
            return True
        else:
            print(f"Task '{task_name}' not found.")
            return False

    # CRUD operations for tasks
    def create_task(self, task_info):
        new_task = Task(task_info['name'], task_info['effect'], task_info['type'], task_info['label'])
        if task_info['name'] in self.all_tasks:
            print(f"Task '{task_info['name']}' already exists.")
            return False
        self.all_tasks[task_info['name']] = {'task': new_task, "completed": False, "count": 0}
        print(f"Task '{task_info['name']}' added.")
        return True

    def delete_task(self, task_name):
        if task_name in self.all_tasks:
            self.all_tasks[task_name] = None
            print(f"Task '{task_name}' removed.")
            return True
        else:
            print(f"Task '{task_name}' not found.")
            return False

    def get_task(self, task_name):
        return self.all_tasks.get(task_name, None)

    def update_task(self, task_name, new_name=None, new_effect=None, new_type=None):
        if task_name in self.all_tasks:
            if new_name:
                new_task_info = {'name': new_name, 
                            'effect': new_effect if new_effect else self.all_tasks[task_name]['effect'], 
                            'type': new_type if new_type else self.all_tasks[task_name]['type']}
                self.create_task(new_task_info)
                self.all_tasks[task_name] = None
            else:
                if new_effect: self.all_tasks[task_name].get('task').set_effect(new_effect)
                if new_type and new_type != self.all_tasks[task_name].get('task').get('type'):
                    self.all_tasks[task_name].get('task').set_type(new_type)
                    self.toggle_task_type(task_name)
            print(f"Task '{task_name}' updated.")
            return True
        else:
            print(f"Task '{task_name}' not found.")
            return False

    # Apply task effects to state
    def apply_task(self, task_name, current_state, multiplier=1):
        task_entry = self.get_task(task_name)
        if task_entry:
            task_obj = task_entry.get('task')
            for key, value in task_obj.effect.items():
                current_state.update_metric(key, value * multiplier)
            print(f"Effects of task '{task_name}' applied to state.")
            return True
        else:
            print(f"Task '{task_name}' not found.")
            return False
        