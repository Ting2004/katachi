# app.py
from nicegui import ui
import json
from datetime import date
from objects.task import TaskList, Task
from objects.state import State, attributes
from utils import load_profile

# ------------------------
# 数据定义
# ------------------------


PROFILE_FILE = './profile.json'
STATE_FILE = './state.json'
TASK_FILE = './tasks.json'

profile = load_profile(PROFILE_FILE)
state = State(filename=STATE_FILE, init=False)
task_list = TaskList(TASK_FILE)



# ------------------------
# UI 界面布局
# ------------------------

# @TODO 页面整体风格更改
color_schemes = {
    'vibrant': {
        'primary': '#5E2Bff',
        'secondary': '#C04CFD',
        'bg': '#F3FAE1',
        'error': '#FC6DAB',
        'accent': '#F7F6C5',
    },
    'plain': {
        'primary': '#003559',
        'secondary': '#006DAA',
        'bg': '#B9D6F2',
        'error': '#061A40',
        'accent': '#0353A4',
    },
    'ppmc': {
        'primary': '#4e6ef2',
        'secondary': '#f28fb1',
        'bg': '#a1d99b',
        'error': '#ff4c4c',
        'accent': '#ffca3a',
    },
    'greyscale': {
        'primary': '#555555',
        'secondary': '#888888',
        'bg': '#DDDDDD',
        'error': '#AA0000',
        'accent': '#777777',
    },
    'warm':{
        'primary': '#EF798A',
        'secondary': '#F7A9A8',
        'bg': '#E5C3D1',
        'error': '#613F75',
        'accent': '#7D82B8',
    }
}

# color_choice = "greyscale"  # 'vibrant', 'plain', 'ppmc', 'greyscale'


with ui.row().classes('w-full justify-between mt-4'):
    ui.label('▲ 僕たちの形').classes('text-2xl font-bold text-center mt-4 mb-4')

    # 配色选择器
    color_choice = ui.select(list(color_schemes.keys()),
            label='配色方案', value='plain',
            on_change=lambda e : ui.colors(**color_schemes[e.value])).props('dense').classes('text-center w-30 flex-none')
ui.colors(**color_schemes[color_choice.value])

with ui.row().classes('w-full justify-center gap-8'):
    
    # -------- 左侧：状态面板 --------
    with ui.column().classes('w-1/3 bg-white/60 p-4 rounded-2xl shadow-md'):
        ui.label('💫 当前状态').classes('text-xl font-semibold mb-2 text-center')
        progress_bars = {}
        for key, value in state.get_state().items():
            ui.label({
                'health': '💪 健康',
                'hydration': '💧 水分',
                'sleep': '😴 睡眠',
                'energy': '⚡ 体力',
                'relax': '🌪️ 放松',
                'focus': '🎯 专注力',
                'mood': '😊 心情',
                'social': '💬 社交能量',
            }[key]).classes('mt-2 font-medium')

            progress_bars[key] = ui.linear_progress(value / 100, show_value=False, size='10px').props('color=primary stripe rounded')
    
    # -------- 右侧：任务区 --------
    def toggle_checkbox(e, task_name: str):
            # 使用 task_name 而不是 task 对象，避免闭包捕获
        if e.value:
            task_list.complete_task(task_name)
            task_list.apply_task(task_name, current_state=state, multiplier=1)
        else:
            task_list.uncomplete_task(task_name)
            # 撤销影响时用 -1
            task_list.apply_task(task_name, current_state=state, multiplier=-1)
        task_list.save_tasks()
        update_status_bar()
        ui.notify(f"任务 '{task_name}' 状态已更新")

    def inc_counter(task_name: str, label):
        task_list.complete_task(task_name)            # count += 1
        task_list.apply_task(task_name, current_state=state, multiplier=1)
        task_list.save_tasks()
        # 更新对应标签文本（读取最新 count）
        entry = task_list.get_task(task_name)
        label.set_text(f"{task_name} × {entry['count']}")
        update_status_bar()

    def dec_counter(task_name: str, label):
        task_list.uncomplete_task(task_name)          # count -= 1 (如果 >0)
        task_list.apply_task(task_name, current_state=state, multiplier=-1)
        task_list.save_tasks()
        entry = task_list.get_task(task_name)
        label.set_text(f"{task_name} × {entry['count']}")
        update_status_bar()

    
    with ui.column().classes('w-1/3 bg-white/60 p-4 rounded-2xl shadow-md'):
        ui.label('📋 任务管理').classes('text-xl font-semibold mb-2 text-center')

        # ---------- Tabs ----------
        with ui.tabs().classes('w-full') as tabs:
            tab_daily = ui.tab('日常生活')
            tab_work = ui.tab('工作学习')
            tab_social = ui.tab('社交娱乐')
            tab_custom = ui.tab('其他')

        # tab_panels: 默认展示 tab_daily
        with ui.tab_panels(tabs, value=tab_daily).classes('w-full') as panels:
            
            def make_refresh_fn(target_panel, label):
                
                def refresh():
                    target_panel.clear()
                    with target_panel:
                        for task_entry in task_list.list_all():
                            if task_entry is None or task_entry.get('task').get_label() != label:
                                continue
                            task = task_entry['task']
                            name = task.get_name()

                            if task.get_type() == 'check':
                                with ui.row().classes('items-center justify-between w-full'):
                                    ui.checkbox(
                                        name,
                                        value=task_entry.get('completed', False),
                                        on_change=lambda e, n=name: toggle_checkbox(e, n)
                                    )
                                    ui.button('×', color='secondary',
                                            on_click=lambda _, n=name: remove_task(n)).props('rounded justify-end')

                            elif task.get_type() == 'counter':
                                with ui.row().classes('items-center justify-between w-full'):
                                    label_widget = ui.label(f"{name} × {task_entry.get('count', 0)}")
                                    with ui.row().classes('justify-end'):
                                        ui.button('+', on_click=lambda _, n=name, l=label_widget: inc_counter(n, l))
                                        ui.button('−', on_click=lambda _, n=name, l=label_widget: dec_counter(n, l))
                                        ui.button('×', color='secondary',
                                                on_click=lambda _, n=name: remove_task(n)).props('rounded justify-end')
                return refresh
            

            # @TODO 固定tab高度，内部作为可滚动
            # @TODO 任务可拖动排序

            # ========== 日常任务面板 ==========
            with ui.tab_panel(tab_daily):
                daily_panel = ui.column().classes('w-full gap-2')
                # @TODO 如果无任务，展示一段占位文字
                # if refresh_task_list(daily_panel, 'daily'):
                #     ui.label('🏠 日常生活相关任务待添加...').classes('text-center text-gray-600 mt-4')
 
            # ========== 工作任务面板 ==========
            with ui.tab_panel(tab_work):
                # ui.label('💼 工作学习相关任务待添加...').classes('text-center text-gray-600 mt-4')
                work_panel = ui.column().classes('w-full gap-2')

            # ========== 社交任务面板 ==========
            with ui.tab_panel(tab_social):
                # ui.label('🎉 社交娱乐相关任务待添加...').classes('text-center text-gray-600 mt-4')
                social_panel = ui.column().classes('w-full gap-2')

            # ========== 自定义任务面板 ==========
            with ui.tab_panel(tab_custom):
                # ui.label('✨ 这里以后可以放自定义模板或任务库').classes('text-center text-gray-600 mt-4')
                custom_panel = ui.column().classes('w-full gap-2')

        refresh_daily = make_refresh_fn(daily_panel, 'daily')
        refresh_work = make_refresh_fn(work_panel, 'work')
        refresh_social = make_refresh_fn(social_panel, 'social')
        refresh_custom = make_refresh_fn(custom_panel, 'custom')

        def refresh_all():
                refresh_daily()
                refresh_work()
                refresh_social()
                refresh_custom()


        def remove_task(task_name: str):
            task_list.apply_task(task_name, current_state=state, multiplier=-task_list.get_task(task_name).get('count', 0))
            task_list.delete_task(task_name)

            task_list.save_tasks()
            task_list.load_tasks()

            update_status_bar()
            ui.notify(f"任务 '{task_name}' 已删除")
            refresh_all()  # 重新刷新列表

            # 添加任务输入区
        
        
        # ========== 新增任务面板 ==========
        ui.separator()
        with ui.row().classes('justify-between items-end mt-4'):
            new_task_name = ui.input(
                label='新任务',
                placeholder='今天需要完成什么任务？'
            ).props('clearable outlined dense').classes('grow w-[230px] flex-none')

            new_task_type = ui.select({'check': '单次任务', 'counter': '多次任务'},
                label='任务类型',
            ).props('outlined dense').classes('w-[150px] flex-none')

            new_task_label = ui.select({'daily': '日常生活', 'work': '工作学习', 'social': '社交娱乐', 'custom': '其他'},
                label='任务标签',
            ).props('outlined dense').classes('w-[150px] flex-none')

        effect_inputs = {}  # 保存 input 对象
        with ui.row().classes('items-center mt-2 gap-2'):
            for attr in attributes:
                # 每个 attribute 一列
                with ui.column().classes('w-24'):
                    ui.label(attr).classes('text-sm text-center')
                    inp = ui.input(value='0', placeholder='0').props('outlined dense')
                    effect_inputs[attr] = inp  # 保存 input 对象，提交时读取


        def add_user_task(e=None):
            name = new_task_name.value.strip()
            ttype = new_task_type.value
            label = new_task_label.value
            if not name or not ttype or not label:
                ui.notify('请输入任务名称与类型 ⚠️')
                return
            effect = {}
            for attr, inp in effect_inputs.items():
                try:
                    val = int(inp.value)
                except ValueError:
                    val = 0
                effect[attr] = val
            # 创建任务
            if task_list.create_task({'name': name, 'type': ttype, 'effect': effect, 'label': label}):

                task_list.save_tasks()
                task_list.load_tasks()
                                                                
                # ✅ 先 notify，再刷新
                ui.notify(f"任务 '{name}' 已添加 ✅")
            else:
                ui.notify(f"任务 '{name}' 已存在 ⭕")

            panel_map = {
                'daily': daily_panel,
                'work': work_panel,
                'social': social_panel,
                'custom': custom_panel}                    
            # refresh_task_list(panel_map[label], label)
            refresh_all()
            #@TODO 添加新任务后切换到对应的tab
            # tabs.set_value(label)  
            # panels.set_value(label)
        
            # 清空输入框
            new_task_name.value = ''
            new_task_type.value = None
            new_task_label.value = None
            for attr, inp in effect_inputs.items():
                inp.value = 0
            

        ui.button('添加', color='primary', on_click=add_user_task).props('rounded')

        refresh_all()  # 初始加载任务列表



ui.separator().classes('my-4')


def reset_task_and_state():
    for task_entry in task_list.list_all():
        task = task_entry['task']
        if task.get_type() == 'check' and task_entry.get('completed', False):
            task_list.apply_task(task.get_name(), current_state=state, multiplier=-1)
        elif task.get_type() == 'counter' and task_entry.get('count', 0) > 0:
            task_list.apply_task(task.get_name(), current_state=state, multiplier=-task_entry.get('count', 0))
    task_list.reset_completion_status(manual_reset=True)

# -------- 页面底部：保存按钮 --------
with ui.row().classes('w-full justify-center py-4 bg-white/70'):
    def save_and_notify():
        state.save_state()
        task_list.save_tasks()
        ui.notify('数据已保存 💾')

    ui.button('保存数据', color='primary', on_click=save_and_notify).props('rounded')

    ui.button('手动重置日常任务', color='primary', on_click=lambda: [reset_task_and_state(), refresh_all(), update_status_bar(), ui.notify('日常任务已重置 🔄')]).props('rounded')
    
    ui.button('重置状态与任务', color='secondary', on_click=lambda: [reset_to_default(state, task_list), refresh_all(), update_status_bar(), ui.notify('状态与任务已重置 ⚠️')]).props('rounded')




# ------------------------
# 更新指标显示函数
# ------------------------

# 存档读档
def save_all():
    state.save_state()
    task_list.save_tasks()
def load_all():
    state.load_state()
    task_list.load_tasks()

# 重置到default配置
def reset_to_default(state, task_list):
    profile = load_profile('./default/default_profile.json')
    tasks = load_profile('./default/default_tasks.json')

    metrics = profile['metrics']
    decay_rates = profile['decay_rates']
    state.set_metrics(metrics)
    state.set_decay_rates(decay_rates)

    task_list.reset_entries(tasks)
    



def update_status_bar():
    for k, bar in progress_bars.items():
        value = state.get_metric(k)  # 0~100
        bar.set_value(value / 100)

def auto_decay_refresh():
    state.apply_decay()
    update_status_bar()
    state.save_state()

def auto_save():
    state.save_state()
    task_list.save_tasks()

ui.timer(10, auto_decay_refresh)  # every 10 second
ui.timer(600, auto_save)  # every 10 miutes
ui.timer(60, task_list.reset_completion_status)


# ------------------------
# 运行应用
# ------------------------
ui.run(title='Self Care App', reload=False)
