import ftplib
import logging
import math
import os
import random
import re
import shutil
import subprocess
import threading
import time
import tkinter as tk
import uuid
from datetime import datetime
from tabulate import tabulate
from colorama import init, Fore, Back, Style

import arrow
import paramiko
import shortuuid
from pyfiglet import Figlet

VERSION = 'v28.12'

BG_COLOR = '#3D3D3D'
SELECT_COLOR = '#28b463'
TXT_COLOR = '#FAE5D3'
TXT_SELECT_COLOR = '#000000'

UNIQ_SN = '#FFD700'
PIRATE_SN = '#228B22'
NOT_CONNECT = '#FF4500'
TXT_BLACK_COLOR = '#000000'

init(autoreset=True)

KEK_SN = '1423219080397'
BUTTON_STATE = {}
for button_number in range(10, 30):
    BUTTON_STATE[f'b_{button_number}'] = False
SSH_LOGIN = "user"
SSH_PWD = "synergo2020"
SSH_PORT = 22
SSH_MIKROTIK_PORT = 25
TIME_OUT = 3
LOCAL_PATH = (os.getcwd()).replace('\\', '/')
KEYCATALOG = (os.path.join(os.getcwd(), 'keycatalog')).replace('\\', '/')
TICKETS = '/opt/AxxonSoft/AxxonNext/Tickets/'
PATH = r'/opt/AxxonSoft/AxxonNext/instance.conf'
BASE_PORT = 20111  # Base port ноды
LICENSE_TYPE = 13  # Universe
COMPLETED_HOST = 0

CNT_N = 0
CNT_P = 0
CNT_U = 0

logging.getLogger("paramiko").setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', '%Y-%m-%d %H:%M:%S')


def setup_logger(name, log_file, level=logging.INFO):
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


nodeNamesLog = setup_logger('nodeNamesLog', 'getNodeNames.log')
synergoTool = setup_logger('synergoTool', 'synergoTool.log')


def _create_default_directories(default_directory):
    if not os.path.exists(default_directory):
        try:
            if os.makedirs(default_directory):
                return True
            else:
                return False
        except Exception as ex:
            synergoTool.error(str(ex))
            return False
    else:
        return True
        # synergoTool.info('Catalog already exists.')


if not _create_default_directories(KEYCATALOG):
    synergoTool.error('Catalog cannot be created ' + KEYCATALOG)


def counting_status():
    global CNT_N, CNT_U, CNT_P
    CNT_N = 0
    CNT_U = 0
    CNT_P = 0
    for label_number in range(10, 30):
        if getattr(m_window, f'l_{label_number}').cget('text') == 'N':
            CNT_N += 1
        elif getattr(m_window, f'l_{label_number}').cget('text') == 'U':
            CNT_U += 1
        elif getattr(m_window, f'l_{label_number}').cget('text') == 'P':
            CNT_P += 1
    getattr(m_window, f'cnt_n_t').configure(text=f': {CNT_N}')
    getattr(m_window, f'cnt_u_t').configure(text=f': {CNT_U}')
    getattr(m_window, f'cnt_p_t').configure(text=f': {CNT_P}')


def setFontColor(string, color):
    text = ''
    if color == 'YELLOW':
        text = Fore.YELLOW + string + Fore.RESET
    if color == 'RED':
        text = Fore.RED + string + Fore.RESET
    if color == 'GREEN':
        text = Fore.GREEN + string + Fore.RESET
    if color == 'CYAN':
        text = Fore.CYAN + string + Fore.RESET
    if color == 'MAGENTA':
        text = Fore.MAGENTA + string + Fore.RESET
    return text


class StartThread:
    def __init__(self, name, target, *args):
        self.name = name
        self.target = target
        self.args = args
        thread = threading.Thread(target=self.target, name=self.name, args=self.args)
        self.thread = thread
        thread.start()


class MainWindow:
    def __init__(self, parent):
        self.parent = parent
        self.parent.title(f'MSVKTOOL {VERSION}')
        # self.parent.wm_attributes('-topmost', True)
        screen_width = self.parent.winfo_screenwidth() // 2
        screen_height = self.parent.winfo_screenheight() // 3
        self.parent.geometry('+{}+{}'.format(screen_width, screen_height))
        self.parent.resizable(False, False)

        # self.parent.attributes('-toolwindow', True)

        def button_press(pressed_button):
            if not BUTTON_STATE[pressed_button]:
                BUTTON_STATE[pressed_button] = True
                getattr(m_window, f'{pressed_button}').configure(bg=SELECT_COLOR)
                getattr(m_window, f'{pressed_button}').configure(activebackground=SELECT_COLOR)
                getattr(m_window, f'{pressed_button}').configure(fg=TXT_SELECT_COLOR)
            else:
                BUTTON_STATE[pressed_button] = False
                getattr(m_window, f'{pressed_button}').configure(bg=BG_COLOR)
                getattr(m_window, f'{pressed_button}').configure(activebackground=BG_COLOR)
                getattr(m_window, f'{pressed_button}').configure(fg=TXT_COLOR)

        def cAll():
            for b_number in range(10, 30):
                pressed_button = f'b_{b_number}'
                if BUTTON_STATE[pressed_button]:
                    BUTTON_STATE[pressed_button] = False
                button_press(pressed_button)

        def unAll():
            for b_number in range(10, 30):
                pressed_button = f'b_{b_number}'
                if not BUTTON_STATE[pressed_button]:
                    BUTTON_STATE[pressed_button] = True
                button_press(pressed_button)

        def button_selection(pressed_label):
            pressed_text = getattr(m_window, f'{pressed_label}').cget('text')
            unAll()
            for label_number in range(10, 30):
                text = getattr(m_window, f'l_{label_number}').cget('text')
                if pressed_text == text:
                    BUTTON_STATE[f'b_{label_number}'] = True
                    getattr(m_window, f'b_{label_number}').configure(bg=SELECT_COLOR)
                    getattr(m_window, f'b_{label_number}').configure(activebackground=SELECT_COLOR)
                    getattr(m_window, f'b_{label_number}').configure(fg=TXT_SELECT_COLOR)

        def reset_status():
            for status_number in range(10, 30):
                getattr(m_window, f'l_{status_number}').configure(bg=BG_COLOR)
                getattr(m_window, f'l_{status_number}').configure(text='  ')
            counting_status()

        def cnt_buttons_flash(button):
            if button == 'plus':
                times = int(m_window.b_flashMikrotik88_times['text'])
                times += 1
                m_window.b_flashMikrotik88_times['text'] = str(times)
            if button == 'minus':
                times = int(m_window.b_flashMikrotik88_times['text'])
                if times > 0:
                    times -= 1
                m_window.b_flashMikrotik88_times['text'] = str(times)

        def cnt_buttons_ip(button):
            if button == 'plus':
                times = int(m_window.b_changeIP_times['text'])
                times += 1
                m_window.b_changeIP_times['text'] = str(times)
            if button == 'minus':
                times = int(m_window.b_changeIP_times['text'])
                if times > 0:
                    times -= 1
                m_window.b_changeIP_times['text'] = str(times)

        def set_buttons_ip(button):
            if button == '15':
                m_window.b_changeIP_times['text'] = str(15)
            if button == '19':
                m_window.b_changeIP_times['text'] = str(19)
            if button == '0':
                m_window.b_changeIP_times['text'] = str(0)

        self.main_frame = tk.Frame(parent, bg=BG_COLOR)
        self.main_frame.grid(row=0, column=0)

        self.button_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        self.button_frame.grid(row=1, column=0)
        self.b_plug = tk.Label(self.main_frame, text='', width=3, bg=BG_COLOR, fg=TXT_COLOR)
        self.b_plug.grid(row=1, column=1, padx=5, pady=5)

        self.cnt_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        self.cnt_frame.grid(row=0, column=0, padx=5, pady=5)

        self.cnt_n = tk.Label(self.cnt_frame, text=f'N', bg=NOT_CONNECT, fg=TXT_COLOR, width=3)
        self.cnt_n.grid(row=0, column=0, padx=5, pady=1)
        self.cnt_n_t = tk.Label(self.cnt_frame, text=f': {CNT_N}', bg=BG_COLOR, fg=TXT_COLOR)
        self.cnt_n_t.grid(row=0, column=1, padx=5, pady=1)
        self.cnt_p = tk.Label(self.cnt_frame, text=f'P', bg=PIRATE_SN, fg=TXT_COLOR, width=3)
        self.cnt_p.grid(row=0, column=4, padx=5, pady=1)
        self.cnt_p_t = tk.Label(self.cnt_frame, text=f': {CNT_P}', bg=BG_COLOR, fg=TXT_COLOR)
        self.cnt_p_t.grid(row=0, column=5, padx=5, pady=1)
        self.cnt_u = tk.Label(self.cnt_frame, text=f'U', bg=UNIQ_SN, fg=TXT_BLACK_COLOR, width=3)
        self.cnt_u.grid(row=0, column=2, padx=5, pady=1)
        self.cnt_u_t = tk.Label(self.cnt_frame, text=f': {CNT_U}', bg=BG_COLOR, fg=TXT_COLOR)
        self.cnt_u_t.grid(row=0, column=3, padx=5, pady=1)

        self.together_tool_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        self.together_tool_frame.grid(row=1, column=2, padx=5, pady=5)

        self.axxon_tool_frame = tk.LabelFrame(self.together_tool_frame, bg=BG_COLOR, fg=TXT_COLOR, text='axxonTools')
        self.axxon_tool_frame.grid(row=0, column=0, padx=5, pady=5)

        self.check_tool_frame = tk.Frame(self.axxon_tool_frame, bg=BG_COLOR)
        self.check_tool_frame.grid(row=0, column=0, padx=5, pady=5)

        self.system_tool_frame = tk.LabelFrame(self.together_tool_frame, bg=BG_COLOR, fg=TXT_COLOR, text='systemTools')
        self.system_tool_frame.grid(row=1, column=0, padx=5, pady=5)
        self.b_plug = tk.Label(self.main_frame, text='', width=3, bg=BG_COLOR, fg=TXT_COLOR)
        self.b_plug.grid(row=1, column=3, padx=5, pady=5)

        # self.key_tool_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        # self.key_tool_frame.grid(row=1, column=4, padx=5, pady=5)
        #
        # self.b_plug = tk.Label(self.main_frame, text='', width=3, bg=BG_COLOR, fg=TXT_COLOR)
        # self.b_plug.grid(row=1, column=5, padx=5, pady=5)
        #
        # self.tool_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        # self.tool_frame.grid(row=1, column=6, padx=5, pady=5)

        self.b_10 = tk.Button(self.button_frame, text='.10', command=lambda: button_press('b_10'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_10.grid(row=0, column=1, padx=5, pady=5)

        self.l_10 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_10.grid(row=0, column=0, padx=5, pady=5)
        self.l_10.bind("<Button-1>", lambda e: button_selection('l_10'))

        self.b_11 = tk.Button(self.button_frame, text='.11', command=lambda: button_press('b_11'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_11.grid(row=1, column=1, padx=5, pady=5)
        self.l_11 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_11.grid(row=1, column=0, padx=5, pady=5)
        self.l_11.bind("<Button-1>", lambda e: button_selection('l_11'))

        self.b_12 = tk.Button(self.button_frame, text='.12', command=lambda: button_press('b_12'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_12.grid(row=2, column=1, padx=5, pady=5)
        self.l_12 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_12.grid(row=2, column=0, padx=5, pady=5)
        self.l_12.bind("<Button-1>", lambda e: button_selection('l_12'))

        self.b_13 = tk.Button(self.button_frame, text='.13', command=lambda: button_press('b_13'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_13.grid(row=3, column=1, padx=5, pady=5)
        self.l_13 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_13.grid(row=3, column=0, padx=5, pady=5)
        self.l_13.bind("<Button-1>", lambda e: button_selection('l_13'))

        self.b_14 = tk.Button(self.button_frame, text='.14', command=lambda: button_press('b_14'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_14.grid(row=4, column=1, padx=5, pady=5)
        self.l_14 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_14.grid(row=4, column=0, padx=5, pady=5)
        self.l_14.bind("<Button-1>", lambda e: button_selection('l_14'))

        self.b_15 = tk.Button(self.button_frame, text='.15', command=lambda: button_press('b_15'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_15.grid(row=5, column=1, padx=5, pady=5)
        self.l_15 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_15.grid(row=5, column=0, padx=5, pady=5)
        self.l_15.bind("<Button-1>", lambda e: button_selection('l_15'))

        self.b_16 = tk.Button(self.button_frame, text='.16', command=lambda: button_press('b_16'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_16.grid(row=6, column=1, padx=5, pady=5)
        self.l_16 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_16.grid(row=6, column=0, padx=5, pady=5)
        self.l_16.bind("<Button-1>", lambda e: button_selection('l_16'))

        self.b_17 = tk.Button(self.button_frame, text='.17', command=lambda: button_press('b_17'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_17.grid(row=7, column=1, padx=5, pady=5)
        self.l_17 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_17.grid(row=7, column=0, padx=5, pady=5)
        self.l_17.bind("<Button-1>", lambda e: button_selection('l_17'))

        self.b_18 = tk.Button(self.button_frame, text='.18', command=lambda: button_press('b_18'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_18.grid(row=8, column=1, padx=5, pady=5)
        self.l_18 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_18.grid(row=8, column=0, padx=5, pady=5)
        self.l_18.bind("<Button-1>", lambda e: button_selection('l_18'))

        self.b_19 = tk.Button(self.button_frame, text='.19', command=lambda: button_press('b_19'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_19.grid(row=9, column=1, padx=5, pady=5)
        self.l_19 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_19.grid(row=9, column=0, padx=5, pady=5)
        self.l_19.bind("<Button-1>", lambda e: button_selection('l_19'))

        self.b_20 = tk.Button(self.button_frame, text='.20', command=lambda: button_press('b_20'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_20.grid(row=0, column=2, padx=5, pady=5)
        self.l_20 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_20.grid(row=0, column=3, padx=5, pady=5)
        self.l_20.bind("<Button-1>", lambda e: button_selection('l_20'))

        self.b_21 = tk.Button(self.button_frame, text='.21', command=lambda: button_press('b_21'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_21.grid(row=1, column=2, padx=5, pady=5)
        self.l_21 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_21.grid(row=1, column=3, padx=5, pady=5)
        self.l_21.bind("<Button-1>", lambda e: button_selection('l_21'))

        self.b_22 = tk.Button(self.button_frame, text='.22', command=lambda: button_press('b_22'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_22.grid(row=2, column=2, padx=5, pady=5)
        self.l_22 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_22.grid(row=2, column=3, padx=5, pady=5)
        self.l_22.bind("<Button-1>", lambda e: button_selection('l_22'))

        self.b_23 = tk.Button(self.button_frame, text='.23', command=lambda: button_press('b_23'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_23.grid(row=3, column=2, padx=5, pady=5)
        self.l_23 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_23.grid(row=3, column=3, padx=5, pady=5)
        self.l_23.bind("<Button-1>", lambda e: button_selection('l_23'))

        self.b_24 = tk.Button(self.button_frame, text='.24', command=lambda: button_press('b_24'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_24.grid(row=4, column=2, padx=5, pady=5)
        self.l_24 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_24.grid(row=4, column=3, padx=5, pady=5)
        self.l_24.bind("<Button-1>", lambda e: button_selection('l_24'))

        self.b_25 = tk.Button(self.button_frame, text='.25', command=lambda: button_press('b_25'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_25.grid(row=5, column=2, padx=5, pady=5)
        self.l_25 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_25.grid(row=5, column=3, padx=5, pady=5)
        self.l_25.bind("<Button-1>", lambda e: button_selection('l_25'))

        self.b_26 = tk.Button(self.button_frame, text='.26', command=lambda: button_press('b_26'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_26.grid(row=6, column=2, padx=5, pady=5)
        self.l_26 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_26.grid(row=6, column=3, padx=5, pady=5)
        self.l_26.bind("<Button-1>", lambda e: button_selection('l_26'))

        self.b_27 = tk.Button(self.button_frame, text='.27', command=lambda: button_press('b_27'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_27.grid(row=7, column=2, padx=5, pady=5)
        self.l_27 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_27.grid(row=7, column=3, padx=5, pady=5)
        self.l_27.bind("<Button-1>", lambda e: button_selection('l_27'))

        self.b_28 = tk.Button(self.button_frame, text='.28', command=lambda: button_press('b_28'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_28.grid(row=8, column=2, padx=5, pady=5)
        self.l_28 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_28.grid(row=8, column=3, padx=5, pady=5)
        self.l_28.bind("<Button-1>", lambda e: button_selection('l_28'))

        self.b_29 = tk.Button(self.button_frame, text='.29', command=lambda: button_press('b_29'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_29.grid(row=9, column=2, padx=5, pady=5)
        self.l_29 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_29.grid(row=9, column=3, padx=5, pady=5)
        self.l_29.bind("<Button-1>", lambda e: button_selection('l_29'))

        self.b_plug = tk.Label(self.button_frame, text='', width=3, bg=BG_COLOR, fg=TXT_COLOR)
        self.b_plug.grid(row=10, column=1, padx=5, pady=5)

        self.b_cAll = tk.Button(self.button_frame, text='All', width=4, command=cAll, bg=BG_COLOR, fg=TXT_COLOR,
                                activebackground=BG_COLOR)
        self.b_cAll.grid(row=11, column=1, padx=5, pady=5)

        self.b_unAll = tk.Button(self.button_frame, text='None', command=unAll, bg=BG_COLOR, fg=TXT_COLOR,
                                 activebackground=BG_COLOR)
        self.b_unAll.grid(row=11, column=2, padx=5, pady=5)
        self.b_reset = tk.Button(self.button_frame, text='   RESET   ', command=reset_status, bg=BG_COLOR, fg=TXT_COLOR,
                                 activebackground=BG_COLOR)
        self.b_reset.grid(row=12, column=1, padx=5, pady=5, columnspan=2)

        self.s_fastNodeName_status = tk.IntVar()
        self.c_fastNodeName_status = tk.Checkbutton(self.check_tool_frame, variable=self.s_fastNodeName_status,
                                                    bg=BG_COLOR)
        self.c_fastNodeName_status.grid(row=0, column=0, padx=5, pady=5)

        self.l_fastNodeName = tk.Label(self.check_tool_frame, text='fastNodename', bg=BG_COLOR, fg=TXT_COLOR)
        self.l_fastNodeName.grid(row=0, column=1, padx=5, pady=5)

        self.b_getNodeName = tk.Button(self.axxon_tool_frame, text='getNodeName', width=15, command=thread_getNodeName,
                                       bg=BG_COLOR, fg=TXT_COLOR,
                                       activebackground=SELECT_COLOR)
        self.b_getNodeName.grid(row=1, column=0, padx=5, pady=5)

        self.b_restartAxxon = tk.Button(self.axxon_tool_frame, text='restartAxxon', width=15,
                                        command=thread_restartAxxon, bg=BG_COLOR, fg=TXT_COLOR,
                                        activebackground=SELECT_COLOR)
        self.b_restartAxxon.grid(row=2, column=0, padx=5, pady=5)

        self.b_changeAltAddr = tk.Button(self.axxon_tool_frame, text='changeAltAddr', width=15,
                                         command=thread_changeAltAddr, bg=BG_COLOR, fg=TXT_COLOR,
                                         activebackground=SELECT_COLOR)
        self.b_changeAltAddr.grid(row=3, column=0, padx=5, pady=5)

        self.b_rebootJetson = tk.Button(self.system_tool_frame, text='rebootJetson', width=15,
                                        command=thread_rebootJetson, bg=BG_COLOR, fg=TXT_COLOR,
                                        activebackground=SELECT_COLOR)
        self.b_rebootJetson.grid(row=0, column=0, padx=5, pady=5)

        # self.b_startSSH = tk.Button(self.system_tool_frame, text='startSSH', width=15,
        #                             command=startSSH, bg=BG_COLOR, fg=TXT_COLOR,
        #                             activebackground=SELECT_COLOR)
        # self.b_startSSH.grid(row=1, column=0, padx=5, pady=5)

        self.b_resetDHCP = tk.Button(self.system_tool_frame, text='resetDHCP', width=15,
                                     command=resetDHCP, bg=BG_COLOR, fg=TXT_COLOR,
                                     activebackground=SELECT_COLOR)
        self.b_resetDHCP.grid(row=2, column=0, padx=5, pady=5)

        # self.b_copyKey = tk.Button(self.system_tool_frame, text='copyKey', width=15, command=copyKey, bg=BG_COLOR,
        #                            fg=TXT_COLOR,
        #                            activebackground=SELECT_COLOR)
        # self.b_copyKey.grid(row=3, column=0, padx=5, pady=5)

        self.b_beepMikrotik = tk.Button(self.system_tool_frame, text='beepMikrotik', width=15, command=beepMikrotik,
                                        bg=BG_COLOR, fg=TXT_COLOR,
                                        activebackground=SELECT_COLOR)
        self.b_beepMikrotik.grid(row=4, column=0, padx=5, pady=5)

        self.b_beepMikrotik = tk.Button(self.system_tool_frame, text='clear', width=15, command=clearConsole,
                                        bg=BG_COLOR, fg=TXT_COLOR,
                                        activebackground=SELECT_COLOR)
        self.b_beepMikrotik.grid(row=5, column=0, padx=5, pady=5)

        # self.f_scriptSwitcher = tk.LabelFrame(self.tool_frame, text='scriptSwitcher', bg=BG_COLOR, fg=TXT_COLOR)
        # self.f_scriptSwitcher.grid(row=0, column=0, padx=5, pady=5)
        #
        # self.b_scriptOn = tk.Button(self.f_scriptSwitcher, text='On', width=4, command=setScriptOn, bg=BG_COLOR,
        #                             fg=TXT_COLOR,
        #                             activebackground=SELECT_COLOR)
        # self.b_scriptOn.grid(row=0, column=0, padx=5, pady=5)
        # self.b_scriptOff = tk.Button(self.f_scriptSwitcher, text='Off', width=4, command=setScriptOff, bg=BG_COLOR,
        #                              fg=TXT_COLOR,
        #                              activebackground=SELECT_COLOR)
        # self.b_scriptOff.grid(row=0, column=1, padx=5, pady=5)
        #
        # self.f_flashMikrotik88 = tk.LabelFrame(self.tool_frame, text='flashMikrotik88', bg=BG_COLOR, fg=TXT_COLOR)
        # self.f_flashMikrotik88.grid(row=1, column=0, padx=5, pady=5)
        #
        # self.b_flashMikrotik88_start = tk.Button(self.f_flashMikrotik88, text='Start', width=13,
        #                                          command=thread_flashMikrotik88, bg=BG_COLOR, fg=TXT_COLOR,
        #                                          activebackground=SELECT_COLOR)
        # self.b_flashMikrotik88_start.grid(row=0, column=0, padx=5, pady=5, columnspan=3)
        #
        # self.b_flashMikrotik88_minus = tk.Button(self.f_flashMikrotik88, text='-', width=2,
        #                                          command=lambda: cnt_buttons_flash('minus'), bg=BG_COLOR, fg=TXT_COLOR,
        #                                          activebackground=SELECT_COLOR)
        # self.b_flashMikrotik88_minus.grid(row=1, column=0, padx=5, pady=5)
        #
        # self.b_flashMikrotik88_times = tk.Label(self.f_flashMikrotik88, text='0', width=2, bg=BG_COLOR, fg=TXT_COLOR)
        # self.b_flashMikrotik88_times.grid(row=1, column=1, padx=5, pady=5)
        #
        # self.b_flashMikrotik88_plus = tk.Button(self.f_flashMikrotik88, text='+', width=2,
        #                                         command=lambda: cnt_buttons_flash('plus'), bg=BG_COLOR, fg=TXT_COLOR,
        #                                         activebackground=SELECT_COLOR)
        # self.b_flashMikrotik88_plus.grid(row=1, column=2, padx=5, pady=5)
        #
        # self.f_changeIP = tk.LabelFrame(self.tool_frame, text='changeIP', bg=BG_COLOR, fg=TXT_COLOR)
        # self.f_changeIP.grid(row=2, column=0, padx=5, pady=5)
        #
        # self.b_changeIP_start = tk.Button(self.f_changeIP, text='Start', width=13, command=changeIP, bg=BG_COLOR,
        #                                   fg=TXT_COLOR,
        #                                   activebackground=SELECT_COLOR)
        # self.b_changeIP_start.grid(row=0, column=0, padx=5, pady=5, columnspan=3)
        #
        # self.b_changeIP_minus = tk.Button(self.f_changeIP, text='-', width=2, command=lambda: cnt_buttons_ip('minus'),
        #                                   bg=BG_COLOR, fg=TXT_COLOR,
        #                                   activebackground=SELECT_COLOR)
        # self.b_changeIP_minus.grid(row=1, column=0, padx=5, pady=5)
        #
        # self.b_changeIP_times = tk.Label(self.f_changeIP, text='0', width=2, bg=BG_COLOR, fg=TXT_COLOR)
        # self.b_changeIP_times.grid(row=1, column=1, padx=5, pady=5)
        #
        # self.b_changeIP_plus = tk.Button(self.f_changeIP, text='+', width=2, command=lambda: cnt_buttons_ip('plus'),
        #                                  bg=BG_COLOR, fg=TXT_COLOR,
        #                                  activebackground=SELECT_COLOR)
        # self.b_changeIP_plus.grid(row=1, column=2, padx=5, pady=5)
        #
        # self.b_changeIP_16 = tk.Button(self.f_changeIP, text='15', width=3, command=lambda: set_buttons_ip('15'),
        #                                bg=BG_COLOR, fg=TXT_COLOR,
        #                                activebackground=SELECT_COLOR)
        # self.b_changeIP_16.grid(row=2, column=0, padx=5, pady=5)
        #
        # self.b_changeIP_20 = tk.Button(self.f_changeIP, text='19', width=3, command=lambda: set_buttons_ip('19'),
        #                                bg=BG_COLOR, fg=TXT_COLOR,
        #                                activebackground=SELECT_COLOR)
        # self.b_changeIP_20.grid(row=2, column=1, padx=5, pady=5)
        #
        # self.b_changeIP_0 = tk.Button(self.f_changeIP, text='0', width=3, command=lambda: set_buttons_ip('0'),
        #                               bg=BG_COLOR, fg=TXT_COLOR,
        #                               activebackground=SELECT_COLOR)
        # self.b_changeIP_0.grid(row=2, column=2, padx=5, pady=5)

        #
        # self.f_uploadKey = tk.Label(self.tool_frame2, text=' ', height=1, bg=BG_COLOR, fg=TXT_COLOR)
        # self.f_uploadKey.grid(row=7, column=0, padx=5, pady=5)

        # self.f_static_nodeName = tk.LabelFrame(self.key_tool_frame, text='staticNodeName', bg=BG_COLOR, fg=TXT_COLOR)
        # self.f_static_nodeName.grid(row=0, column=0, padx=5, pady=5)
        # self.s_static_nodeName_status = tk.IntVar()
        # self.c_static_nodeName = tk.Checkbutton(self.f_static_nodeName, variable=self.s_static_nodeName_status,
        #                                         bg=BG_COLOR)
        # self.c_static_nodeName.grid(row=0, column=0, padx=5, pady=5)
        # self.t_static_nodeName = tk.Entry(self.f_static_nodeName, bg=BG_COLOR)
        # self.t_static_nodeName.insert(0, 'JrB6fmrkfjMiJno')
        # self.t_static_nodeName.grid(row=0, column=1, padx=5, pady=5)
        #
        # self.f_changeNodeName = tk.LabelFrame(self.key_tool_frame, text='Step 1', bg=BG_COLOR, fg=TXT_COLOR)
        # self.f_changeNodeName.grid(row=1, column=0, padx=5, pady=5)
        # self.b_changeNodeName = tk.Button(self.f_changeNodeName, text='changeNodeName', width=15,
        #                                   command=changeNodeName, bg=BG_COLOR, fg=TXT_COLOR,
        #                                   activebackground=SELECT_COLOR)
        # self.b_changeNodeName.grid(row=0, column=0, padx=5, pady=5)
        #
        # self.f_collectHID = tk.LabelFrame(self.key_tool_frame, text='Step 2', bg=BG_COLOR, fg=TXT_COLOR)
        # self.f_collectHID.grid(row=2, column=0, padx=5, pady=5)
        # self.b_collectHID = tk.Button(self.f_collectHID, text='collectHID', width=15, command=collectHID, bg=BG_COLOR,
        #                               fg=TXT_COLOR,
        #                               activebackground=SELECT_COLOR)
        # self.b_collectHID.grid(row=0, column=0, padx=5, pady=5)
        #
        # self.f_uploadKey = tk.LabelFrame(self.key_tool_frame, text='Step 3', bg=BG_COLOR, fg=TXT_COLOR)
        # self.f_uploadKey.grid(row=3, column=0, padx=5, pady=5)
        # self.b_uploadKey = tk.Button(self.f_uploadKey, text='uploadKey', width=15, command=uploadKey, bg=BG_COLOR,
        #                              fg=TXT_COLOR, activebackground=SELECT_COLOR)
        # self.b_uploadKey.grid(row=0, column=0, padx=5, pady=5)


def thread_getNodeName():
    print('getNodeName')

    def send_cmd(ssh_client, ip, cmd_name, cmd_sn, cmd_hdd_sn, cmd_date):

        """
        Данный метод предназначен для выполнения консольных команд нерутовым пользователем
        """
        channel = ssh_client.get_transport().open_session()
        channel.get_pty()
        channel.settimeout(5.0)
        channel.exec_command(cmd_name)
        answer = channel.recv(999).decode('utf-8')
        name = ''
        alt_addr = ''
        serial_number = ''
        onvifserver = onvifserver = setFontColor('NotExist', 'RED')
        hdd_sn = ''
        jetson_date = ''
        global CNT_U
        global CNT_P
        if f'password for {SSH_LOGIN}' in answer:
            channel.send(SSH_PWD + '\n')
            time.sleep(2)
            answer_node = channel.recv(999).decode('utf-8')
            for line in answer_node.split('\n'):
                if 'NGP_NODE_NAME' in line:
                    # print(line)
                    parts = line.split('=')
                    name = parts[1].replace('"', '')
                    if 'USER-DESKTOP' in name:
                        name = setFontColor('USER-DESKTOP', 'YELLOW')
                    else:
                        name = setFontColor(name.strip(), 'GREEN')
                if 'NGP_ALT_ADDR' in line:
                    # print(line)
                    parts = line.split('=')
                    alt_addr = parts[1].replace('"', '')
                if 'NGP_ONVIFSERVER_ENDPOINT' in line:
                    # print('NGP_ONVIFSERVER_ENDPOINT EXIST')
                    onvifserver = setFontColor('Exist', 'GREEN')
                    # print(re.search(r'"(.+?)\"', line).group(1))
        # print("\n")
        channel.close()
        if m_window.s_fastNodeName_status.get() == 0:
            channel = ssh_client.get_transport().open_session()
            channel.get_pty()
            channel.settimeout(5.0)
            channel.exec_command(cmd_sn)
            serial_number = channel.recv(999).decode('utf-8').strip()
            serial_number = serial_number.replace('\x00', '').strip()
            if serial_number == KEK_SN:
                serial_number = setFontColor('---> WARNING ---> ', 'RED') + setFontColor(serial_number,
                                                                                         'GREEN') + setFontColor(
                    ' <--- WARNING <---', 'RED')
                getattr(m_window, f'l_{ip}').configure(bg=PIRATE_SN)
                getattr(m_window, f'l_{ip}').configure(text='P')
                counting_status()
            else:
                # print('SN: ' + serial_number)
                serial_number = setFontColor(f'{serial_number}', 'YELLOW')
                getattr(m_window, f'l_{ip}').configure(bg=UNIQ_SN)
                getattr(m_window, f'l_{ip}').configure(text='U')
                counting_status()
            channel.close()

            channel = ssh_client.get_transport().open_session()
            channel.get_pty()
            channel.settimeout(5.0)
            channel.exec_command(cmd_hdd_sn)
            hdd_sn = channel.recv(999).decode('utf-8')
            parts = hdd_sn.split('=')
            hdd_sn = parts[1]
            # print('HDD_SN: ' + hdd_sn)
            channel.close()

            channel = ssh_client.get_transport().open_session()
            channel.get_pty()
            channel.settimeout(5.0)
            channel.exec_command(cmd_date)
            jetson_date = channel.recv(999).decode('utf-8')
            # print('DATE: ' + jetson_date + '\n')
            channel.close()
        return [name, serial_number, alt_addr, onvifserver, hdd_sn, jetson_date]

    def getNodeName():
        global CNT_N
        host_to_restart = []
        for ip in range(10, 30):
            if BUTTON_STATE[f'b_{ip}']:
                host_to_restart.append(ip)
        print(f'Hosts to get: {host_to_restart}\n')
        now = datetime.now()
        nodeNamesLog.info(now.strftime("%d-%m-%Y_%H-%M-%S"))
        for ip in host_to_restart:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                print(f'10.10.10.{ip}')
                client.connect(hostname=f'10.10.10.{ip}', username=SSH_LOGIN, password=SSH_PWD, timeout=TIME_OUT)
                answers = send_cmd(client, ip, 'sudo cat ~ngp/instance.conf',
                                   'cat /sys/firmware/devicetree/base/serial-number',
                                   'udevadm info --query=all --name=/dev/mmcblk0 | grep ID_SERIAL',
                                   'date')

                print(tabulate(
                    [['NODENAME', answers[0]], ['SN', answers[1]], ['ALT_ADDR', answers[2]], ['HDD_SN', answers[4]],
                     ['ONVIFSERVER', answers[3]], ['JETSONDATE', answers[5]]]))
                print('\n')

                nodeNamesLog.info(
                    f'10.10.10.{ip} {answers[0]} SN: {answers[1]} ALT_ADDR: {answers[2]} HDD_SN: {answers[4]} ONVIFSERVER: {answers[3]} JETSONDATE: {answers[5]}')
                client.close()
            except Exception as error:
                print(f'{error}')
                getattr(m_window, f'l_{ip}').configure(bg=NOT_CONNECT)
                getattr(m_window, f'l_{ip}').configure(text='N')
                counting_status()
        print('getNodeName complete')

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'thread_getNodeName':
            find_thread = thread
            print('already thread_getNodeName')
    if find_thread is None:
        StartThread('thread_getNodeName', getNodeName)


def thread_restartAxxon():
    print('restartAxxon')

    def send_cmd(ssh_client, cmd, password=SSH_PWD):
        """
        Данный метод предназначен для выполнения консольных команд нерутовым пользователем
        """
        channel = ssh_client.get_transport().open_session()
        channel.get_pty()
        channel.settimeout(5.0)
        channel.exec_command(cmd)
        answer = channel.recv(999).decode('utf-8')
        if f'password for {SSH_LOGIN}' in answer:
            channel.send(password + '\n')
        status = channel.recv_exit_status()
        channel.close()
        return status

    def restart_Axxon(ip):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            print(f'10.10.10.{ip}')
            client.connect(hostname=f'10.10.10.{ip}', username=SSH_LOGIN, password=SSH_PWD, timeout=TIME_OUT)
            send_cmd(client, 'sudo systemctl restart axxon-next')
            print(f'Restart .{ip} complete')
            client.close()
        except Exception as error:
            print(f'{error}')

    def thread_restart():
        host_to_restart = []
        for ip in range(10, 30):
            if BUTTON_STATE[f'b_{ip}']:
                host_to_restart.append(ip)
        print(f'Hosts to restart: {host_to_restart}\n')
        for ip in host_to_restart:
            StartThread(f'thread_restart_{ip}', restart_Axxon, ip)

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'thread_restartAxxon':
            print('already thread_restartAxxon')
            find_thread = thread
    if find_thread is None:
        StartThread('thread_restartAxxon', thread_restart)


def thread_rebootJetson():
    print('rebootJetson')

    def send_cmd(ssh_client, cmd, password=SSH_PWD):
        """
        Данный метод предназначен для выполнения консольных команд нерутовым пользователем
        """
        channel = ssh_client.get_transport().open_session()
        channel.get_pty()
        channel.settimeout(5.0)
        channel.exec_command(cmd)
        answer = channel.recv(999).decode('utf-8')
        if f'password for {SSH_LOGIN}' in answer:
            channel.send(password + '\n')
        status = channel.recv_exit_status()
        channel.close()
        return status

    def restart_Axxon(ip):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            print(f'10.10.10.{ip}')
            client.connect(hostname=f'10.10.10.{ip}', username=SSH_LOGIN, password=SSH_PWD, timeout=TIME_OUT)
            send_cmd(client, 'sudo reboot')
            print(f'Reboot .{ip} complete')
            client.close()
        except Exception as error:
            print(f'{error}')

    def thread_restart():
        host_to_restart = []
        for ip in range(10, 30):
            if BUTTON_STATE[f'b_{ip}']:
                host_to_restart.append(ip)
        print(f'Hosts to reboot: {host_to_restart}\n')
        for ip in host_to_restart:
            StartThread(f'thread_reboot_{ip}', restart_Axxon, ip)

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'thread_rebootJetson':
            print('already thread_rebootJetson')
            find_thread = thread
    if find_thread is None:
        StartThread('thread_rebootJetson', thread_restart)


def thread_changeAltAddr():
    print('changeAltAddr')

    def send_cmd(ssh_client, cmd, password=SSH_PWD):
        """
        Данный метод предназначен для выполнения консольных команд нерутовым пользователем
        """
        channel = ssh_client.get_transport().open_session()
        channel.get_pty()
        channel.settimeout(5.0)
        channel.exec_command(cmd)
        answer = channel.recv(999).decode('utf-8')
        if f'password for {SSH_LOGIN}' in answer:
            channel.send(password + '\n')
        status = channel.recv_exit_status()
        channel.close()
        return status

    def change_AltAddr(ip):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            print(f'10.10.10.{ip}')
            client.connect(hostname=f'10.10.10.{ip}', username=SSH_LOGIN, password=SSH_PWD, timeout=TIME_OUT)
            cmd = "sudo sed -i '" + 's/NGP_ALT_ADDR=.*/NGP_ALT_ADDR="${' + f'NGP_ALT_ADDR:-10.10.10.{ip}' + '}"/\' ~ngp/instance.conf'
            send_cmd(client, cmd)
            print(f'Change .{ip} complete')
            client.close()
        except Exception as error:
            print(f'{error}')

    def thread_change():
        host_to_restart = []
        for ip in range(10, 30):
            if BUTTON_STATE[f'b_{ip}']:
                host_to_restart.append(ip)
        print(f'Hosts to change: {host_to_restart}\n')
        for ip in host_to_restart:
            StartThread(f'thread_change_{ip}', change_AltAddr, ip)

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'thread_changeAltAddr':
            print('already thread_changeAltAddr')
            find_thread = thread
    if find_thread is None:
        StartThread('thread_changeAltAddr', thread_change)


def beepMikrotik():
    print('start beepMikrotik')

    def thread_beep():
        status_ips = {}
        IPS = []
        result_ssh = False
        cl = paramiko.SSHClient()
        cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        command = ':for i from=1 to=25 do={ :beep ;:delay 0.5}'

        for ip in range(10, 30):
            if BUTTON_STATE[f'b_{ip}']:
                IPS.append(f'10.10.10.{ip}')
        print(IPS)
        if len(IPS) > 1:
            print('Too much for beep. Choose one')
            return
        if len(IPS) < 1:
            print('Choose one for beep')
            return
        if len(IPS) == 1:
            try:
                cl = paramiko.SSHClient()
                cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                print(f"=BEEP= Try connect SSH {IPS[0]}")
                cl.connect(IPS[0], username='admin', password='synergo2020', port=SSH_MIKROTIK_PORT,
                           look_for_keys=False, allow_agent=False)
                print(f"=BEEP= Connect SSH successful {IPS[0]}")
                result_ssh = True
            except Exception:
                print(f"=BEEP= Connect SSH failed {IPS[0]}")
                return
            if result_ssh:
                print(f"=BEEP= Send command {IPS[0]}")
                cl.exec_command(command)
                time.sleep(10)
                cl.close()

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'thread_beep':
            print('already thread_beep')
            find_thread = thread
    if find_thread is None:
        StartThread('thread_beep', thread_beep)


def resetDHCP():
    print('start resetDHCP')
    cmd_disable = '/ip dhcp-server disable defconf'
    cmd_remove = '/ip dhcp-server lease remove numbers=0'
    cmd_enable = '/ip dhcp-server enable defconf'

    def fresetDHCP(ip):
        try:
            cl = paramiko.SSHClient()
            cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            print(f"=resetDHCP= Try connect SSH 10.10.10.{ip}")
            cl.connect(f'10.10.10.{ip}', username='admin', password='synergo2020', port=SSH_MIKROTIK_PORT,
                       look_for_keys=False, allow_agent=False)
            print(f"=resetDHCP= Connect SSH successful 10.10.10.{ip}")
            cl.exec_command(cmd_disable)
            time.sleep(0.5)
            cl.exec_command(cmd_remove)
            time.sleep(0.5)
            cl.exec_command(cmd_enable)
        except Exception as error:
            print(f'{error}')

    def thread_fresetDHCP():
        host_to_restart = []
        for ip in range(10, 30):
            if BUTTON_STATE[f'b_{ip}']:
                host_to_restart.append(ip)
        print(f'Hosts to resetDHCP: {host_to_restart}\n')
        for ip in host_to_restart:
            StartThread(f'thread_resetDHCP_{ip}', fresetDHCP, ip)

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'thread_resetDHCP':
            print('already thread_resetDHCP')
            find_thread = thread
    if find_thread is None:
        StartThread('thread_resetDHCP', thread_fresetDHCP)


def clearConsole():
    os.system('cls')


if __name__ == "__main__":
    main_window = tk.Tk()
    m_window = MainWindow(main_window)
    f = Figlet()
    print(f.renderText(f'MSVK TOOLS {VERSION} SHORT'))
    main_window.mainloop()
