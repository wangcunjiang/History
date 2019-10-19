import random
import traceback, math

from PyQt5.QtCore import QRect, QPoint, QSize
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QPolygon, QFontMetrics
from PyQt5.QtWidgets import QLineEdit, QAbstractItemView, QFileDialog, QCheckBox, QWidget, QLabel, QTextEdit, \
    QTabWidget, QComboBox, QGridLayout

from core import *
from editor import *
from Utility.ui_utility import *


def upper_rough(num):
    abs_num = abs(num)
    index_10 = math.log(abs_num, 10)
    round_index_10 = math.floor(index_10)
    scale = math.pow(10, round_index_10)
    if num >= 0:
        integer = math.ceil(abs_num / scale)
    else:
        integer = math.floor(abs_num / scale)
    rough = integer * scale
    result = rough if num >= 0 else -rough
    return result


def lower_rough(num):
    abs_num = abs(num)
    if abs_num == 0:
        return 0
    index_10 = math.log(abs_num, 10)
    round_index_10 = math.floor(index_10)
    scale = math.pow(10, round_index_10)
    if num >= 0:
        integer = math.floor(abs_num / scale)
    else:
        integer = math.ceil(abs_num / scale)
    rough = integer * scale
    result = rough if num >= 0 else -rough
    return result


def scale_round(num: float, scale: float):
    return (round(num / scale) + 1) * scale


# ------------------------------------------------------- Colors -------------------------------------------------------

# From: https://www.icoa.cn/a/512.html

AXIS_BACKGROUND_COLORS = [QColor(255, 245, 247), QColor(254, 67, 101), QColor(252, 157, 154),
                          QColor(249, 205, 173), QColor(200, 200, 169), QColor(131, 175, 155)]
THREAD_BACKGROUND_COLORS = [QColor(182, 194, 154), QColor(138, 151, 123), QColor(244, 208, 0), QColor(229, 87, 18),
                            QColor(178, 200, 187), QColor(69, 137, 148), QColor(117, 121, 74), QColor(114, 83, 52),
                            QColor(130, 57, 53), QColor(137, 190, 178), QColor(201, 211, 140), QColor(222, 156, 83),
                            QColor(160, 90, 124), QColor(101, 147, 74), QColor(64, 116, 52), QColor(222, 125, 44)]


# --------------------------------------------------- class TimeAxis ---------------------------------------------------

class TimeAxis(QWidget):
    LAYOUT_HORIZON = 1
    LAYOUT_VERTICAL = 2
    ALIGN_LEFT = 4
    ALIGN_RIGHT = 8

    class Thread:
        REFERENCE_TRACK_WIDTH = 50

        def __init__(self):
            self.__event_indexes = []
            self.__paint_indexes = []
            self.__indexes_layout = []
            self.__indexes_adapt_rect = []

            self.__since = 0.0
            self.__until = 0.0
            self.__layout = TimeAxis.LAYOUT_VERTICAL
            self.__thread_width = 0
            self.__thread_length = 0
            self.__thread_track_count = 0
            self.__thread_track_width = 50
            self.__paint_area = QRect(0, 0, 0, 0)

            self.__event_font = QFont()
            self.__event_font.setFamily("微软雅黑")
            self.__event_font.setPointSize(6)

            self.__period_font = QFont()
            self.__period_font.setFamily("微软雅黑")
            self.__period_font.setPointSize(8)

            self.__event_bk = QColor(243, 244, 246)
            self.__story_bk = QColor(185, 227, 217)
            self.__paint_color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        # -------------------------------------------------- Methods ---------------------------------------------------

        def set_thread_color(self, color):
            self.__paint_color = color

        def set_thread_horizon(self, horizon: bool):
            self.__layout = TimeAxis.LAYOUT_HORIZON if horizon else TimeAxis.LAYOUT_VERTICAL
            self.calc_paint_parameters()

        def set_thread_event_indexes(self, indexes: list):
            self.__event_indexes = indexes
            self.calc_paint_parameters()

        def index_from_point(self, point: QPoint):
            for i in reversed(range(0, len(self.__indexes_adapt_rect))):
                if self.__indexes_adapt_rect[i].contains(point):
                    return self.__paint_indexes[i] if i < len(self.__paint_indexes) else None
            return None

        # ---------------------------------------------- Paint Parameters ----------------------------------------------

        def on_paint_canvas_size_update(self, area: QRect):
            self.__paint_area = area
            # Reserved space
            self.__paint_area.setLeft(self.__paint_area.left() + 20)
            self.calc_paint_parameters()

        def on_paint_scale_range_updated(self, since: float, until: float):
            self.__since = since
            self.__until = until
            self.calc_paint_parameters()

        def calc_paint_parameters(self):
            if self.__layout == TimeAxis.LAYOUT_HORIZON:
                self.__thread_width = self.__paint_area.height()
                self.__thread_length = self.__paint_area.width()
            else:
                self.__thread_width = self.__paint_area.width()
                self.__thread_length = self.__paint_area.height()

            self.__paint_indexes.clear()
            self.__indexes_layout.clear()
            self.__indexes_adapt_rect.clear()

            if self.__thread_width < TimeAxis.Thread.REFERENCE_TRACK_WIDTH * 0.3:
                return

            # Adjust track count
            self.__thread_track_count = self.__thread_width / TimeAxis.Thread.REFERENCE_TRACK_WIDTH
            self.__thread_track_count = int(self.__thread_track_count + 0.5)
            self.__thread_track_width = self.__thread_width / self.__thread_track_count

            for index in self.__event_indexes:
                if index.period_adapt(self.__since, self.__until):
                    self.__paint_indexes.append(index)
                    # Pre-allocation
                    self.__indexes_layout.append(-1)
                    self.__indexes_adapt_rect.append(QRect(0, 0, 0, 0))
            self.__paint_indexes = sorted(self.__paint_indexes, key=lambda x: x.since())

            self.layout_event_to_track()

        def layout_event_to_track(self):
            # track_list = []
            # for i in range(0, self.__thread_track_count):
            #     track_list.append(None)

            # Track 1 is reserved for events
            # Layout the low level track first

            for i in range(1, self.__thread_track_count):
                track_place = None
                for j in range(0, len(self.__paint_indexes)):
                    # Already layout
                    if self.__indexes_layout[j] >= 0:
                        continue
                    index = self.__paint_indexes[j]
                    if index.since() == index.until():      # Event
                        self.__indexes_layout[j] = 0
                    else:
                        # Default layout to the last track
                        if track_place is None or index.since() >= track_place or (i == self.__thread_track_count - 1):
                            self.__indexes_layout[j] = i
                            track_place = index.until()

                # for i in range(0, self.__thread_track_count):
                #     # Default layout to the last track
                #     if track_list[i] is None or index.since() > track_list[i] or (i == self.__thread_track_count - 1):
                #         self.__indexes_layout.append(i)
                #         track_list[i] = index.until()
                #         break

        def value_to_pixel(self, value: float):
            if self.__until - self.__since == 0:
                return 0
            return self.__thread_length * (value - self.__since) / (self.__until - self.__since)

        def repaint(self, qp: QPainter):

            qp.setBrush(self.__paint_color)
            qp.drawRect(self.__paint_area)

            if self.__layout == TimeAxis.LAYOUT_HORIZON:
                self.paint_horizon(qp)
            else:
                self.paint_vertical(qp)

        def paint_horizon(self):
            pass

        def paint_vertical(self, qp: QPainter):
            if len(self.__indexes_layout) != len(self.__paint_indexes):
                print('Index and layout mismatch. Something wrong in the layout calculation.')
                return

            overlap_count = 0
            prev_index_area = None

            for i in range(0, len(self.__paint_indexes)):
                index = self.__paint_indexes[i]
                track = self.__indexes_layout[i]

                top = self.__paint_area.top() + self.value_to_pixel(index.since())
                left = self.__paint_area.left() + track * self.__thread_track_width
                right = left + self.__thread_track_width

                if index.since() == index.until():
                    diagonal = right - left
                    half_diagonal = diagonal / 2
                    # v_mid = top
                    # h_mid = left + half_diagonal
                    index_rect = QRect(left, top - half_diagonal, diagonal, diagonal)
                    self.adjust_shape_area(index_rect)
                else:
                    bottom = self.__paint_area.top() + self.value_to_pixel(index.until())
                    index_rect = QRect(left, top, right - left, bottom - top)

                if prev_index_area is not None and index_rect == prev_index_area:
                    overlap_count += 1
                else:
                    overlap_count = 0
                prev_index_area = index_rect

                self.adjust_shape_area(index_rect)
                index_rect = index_rect.translated(0, -3 * overlap_count)
                self.__indexes_adapt_rect[i] = index_rect

                if index.since() == index.until():
                    TimeAxis.Thread.paint_event_bar(qp, index_rect, self.__event_bk)
                    TimeAxis.Thread.paint_index_text(qp, index, index_rect, self.__event_font)
                else:
                    TimeAxis.Thread.paint_period_bar(qp, index_rect, self.__story_bk)
                    TimeAxis.Thread.paint_index_text(qp, index, index_rect, self.__period_font)

        def adjust_shape_area(self, area: QRect) -> QRect:
            if area.top() < self.__paint_area.top():
                area.setTop(self.__paint_area.top())
            if area.bottom() > self.__paint_area.bottom():
                area.setBottom(self.__paint_area.bottom())
            return area

        @staticmethod
        def paint_event_bar(qp: QPainter, index_rect: QRect, back_ground: QColor):
            arrow_points = [QPoint(index_rect.left() - 10, index_rect.center().y()),
                            index_rect.topLeft(), index_rect.topRight(),
                            index_rect.bottomRight(), index_rect.bottomLeft()]
            qp.setBrush(back_ground)
            qp.drawPolygon(QPolygon(arrow_points))

            # diamond_points = [QPoint(left, v_mid), QPoint(h_mid, v_mid - half_diagonal),
            #                   QPoint(right, v_mid), QPoint(h_mid, v_mid + half_diagonal)]
            # qp.setBrush(self.__event_bk)
            # qp.drawPolygon(QPolygon(diamond_points))

        @staticmethod
        def paint_period_bar(qp: QPainter, index_rect: QRect, back_ground: QColor):
            qp.setBrush(back_ground)
            qp.drawRect(index_rect)

        @staticmethod
        def paint_index_text(qp: QPainter, index: HistoricalRecord, index_rect: QRect, font: QFont):
                # qp.save()
                # qp.translate(rect.center())
                # qp.rotate(-90)
                # text_rect = QRect(rect)
                # if text_rect.top() < 0:
                #     text_rect.setTop(0)
                qp.setPen(Qt.SolidLine)
                qp.setPen(QPen(Qt.black, 1))
                qp.setFont(font)

                abstract_tags = index.get_tags('abstract')
                abstract = abstract_tags[0] if len(abstract_tags) > 0 else ''
                qp.drawText(index_rect, Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextWordWrap, abstract)
                # qp.restore()

    # ------------------------------------------------------------------------------------------
    # ------------------------------------- TimeAxis Start -------------------------------------
    # ------------------------------------------------------------------------------------------

    STEP_LIST = [
        10000, 5000, 2500, 2000, 1000, 500, 250, 200, 100, 50, 25, 20, 10, 5, 1, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01
    ]

    DEFAULT_MARGIN_PIXEL = 0
    MAIN_SCALE_MIN_PIXEL = 50

    def __init__(self):
        super(TimeAxis, self).__init__()

        self.__width = 0
        self.__height = 0
        self.__axis_width = 0
        self.__axis_length = 0

        self.__axis_mid = 0
        self.__axis_space_w = 30
        self.__axis_align_offset = 0.3

        self.__thread_width = 0
        self.__thread_left_area = QRect(0, 0, 0, 0)
        self.__thread_right_area = QRect(0, 0, 0, 0)

        self.__offset = 0.0
        self.__scroll = 0.0

        self.__scale_per_page = 10
        self.__pixel_per_scale = 0

        self.__paint_since_scale = 0
        self.__paint_until_scale = 0
        self.__paint_start_scale = 0
        self.__paint_start_offset = 0

        self.__l_pressing = False
        self.__l_down_point = None

        # Real time tips

        self.__tip_font = QFont()
        self.__tip_font.setFamily("微软雅黑")
        self.__tip_font.setPointSize(8)

        self.__enable_real_time_tips = True
        self.__mouse_on_index = HistoricalRecord()
        self.__mouse_on_scale_value = 0.0
        self.__mouse_on_coordinate = QPoint(0, 0)

        self.__era = ''
        self.__layout = TimeAxis.LAYOUT_VERTICAL

        self.__step_selection = 0
        self.__main_step = 0
        self.__sub_step = 0

        self.setMinimumWidth(400)
        self.setMinimumHeight(500)

        self.set_time_range(0, 2000)

        self.setMouseTracking(True)

        self.__history_core = None
        self.__history_editor = None
        self.__history_threads = []

    # ----------------------------------------------------- Method -----------------------------------------------------

    def set_era(self, era: str):
        self.__era = era

    def set_offset(self, offset: float):
        if 0.0 <= offset <= 1.0:
            self.__offset = offset
        self.repaint()

    def set_horizon(self):
        self.__layout = TimeAxis.LAYOUT_HORIZON
        self.repaint()

    def set_vertical(self):
        self.__layout = TimeAxis.LAYOUT_VERTICAL
        self.repaint()

    def set_time_range(self, since: float, until: float):
        self.auto_scale(min(since, until), max(since, until))
        self.repaint()

    def set_history_core(self, history: History):
        self.__history_core = history

    def get_history_threads(self) -> list:
        return self.__history_threads

    def add_history_thread(self, thread):
        if thread not in self.__history_threads:
            self.__history_threads.append(thread)

    def remove_history_threads(self, thread):
        if thread in self.__history_threads:
            self.__history_threads.remove(thread)

    def remove_all_history_threads(self):
        self.__history_threads.clear()
        self.repaint()

    def enable_real_time_tips(self, enable: bool):
        self.__enable_real_time_tips = enable

    # --------------------------------------------------- UI Action ----------------------------------------------------

    def mousePressEvent(self,  event):
        if event.button() == QtCore.Qt.LeftButton:
            self.__l_pressing = True
            self.__l_down_point = event.pos()

    def mouseReleaseEvent(self,  event):
        if event.button() == QtCore.Qt.LeftButton:
            self.__l_pressing = False
            self.__scroll += self.__offset
            self.__offset = 0
            self.repaint()

    def mouseDoubleClickEvent(self,  event):
        now_pos = event.pos()
        index = self.index_from_point(now_pos)
        if index is not None:
            self.popup_editor_for_index(index)

    def mouseMoveEvent(self, event):
        now_pos = event.pos()
        if self.__l_pressing and self.__l_down_point is not None:
            if self.__layout == TimeAxis.LAYOUT_HORIZON:
                self.__offset = self.__l_down_point.x() - now_pos.x()
            else:
                self.__offset = self.__l_down_point.y() - now_pos.y()
            self.repaint()
        else:
            self.on_pos_updated(now_pos)

    def wheelEvent(self, event):
        angle = event.angleDelta() / 8
        angle_x = angle.x()
        angle_y = angle.y()

        modifiers = QApplication.keyboardModifiers()

        if modifiers == QtCore.Qt.ControlModifier:
            # Get the value before step update
            current_pos = event.pos()
            current_pos_offset = self.calc_point_to_paint_start_offset(current_pos)
            current_pos_scale_value = self.pixel_offset_to_scale_value(current_pos_offset)

            self.select_step_scale(self.__step_selection + (1 if angle_y > 0 else -1))

            # Make the value under mouse keep the same place on the screen
            total_pixel_offset = self.__pixel_per_scale * current_pos_scale_value / self.__main_step
            total_pixel_offset -= current_pos_offset
            self.__scroll = total_pixel_offset - self.__offset
        else:
            self.__scroll += (1 if angle_y < 0 else -1) * self.__pixel_per_scale / 4

        self.repaint()

    # ----------------------------------------------------- Action -----------------------------------------------------

    def popup_editor_for_index(self, index: HistoricalRecord):
        if index is None:
            print('None index.')
            return

        # if index.get_focus_label() == 'index':
        #     source = index.source()
        #     if source is None or source == '':
        #         print('Source is empty.')
        #         return
        #     loader = HistoricalRecordLoader()
        #     if not loader.from_source(source):
        #         print('Load source error : ' + source)
        #         return
        #     records = loader.get_loaded_records()
        #     self.update_records(records)
        # else:
        #     # It's a full record
        #     records = [index]

        self.__history_editor = HistoryEditorDialog(editor_agent=self)
        self.__history_editor.get_history_editor().edit_source(index.source(), index.uuid())
        self.__history_editor.show_browser(False)
        self.__history_editor.exec()

    # ----------------------------------------------------- Paint ------------------------------------------------------

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        wnd_size = self.size()
        self.__width = wnd_size.width()
        self.__height = wnd_size.height()

        self.__axis_width = self.__height if self.__layout == TimeAxis.LAYOUT_HORIZON else self.__width
        self.__axis_length = self.__width if self.__layout == TimeAxis.LAYOUT_HORIZON else self.__height
        self.__axis_length -= self.DEFAULT_MARGIN_PIXEL * 2

        self.update_pixel_per_scale()
        self.calc_paint_parameters()
        self.calc_paint_layout()

        self.paint_background(qp)

        if self.__layout == TimeAxis.LAYOUT_HORIZON:
            self.paint_horizon(qp)
        else:
            self.paint_vertical(qp)
        self.paint_threads(qp)
        self.paint_real_time_tips(qp)

        qp.end()

    def paint_background(self, qp: QPainter):
        qp.setBrush(AXIS_BACKGROUND_COLORS[2])
        qp.drawRect(0, 0, self.__width, self.__height)

    def paint_horizon(self, qp: QPainter):
        pass

    def paint_vertical(self, qp: QPainter):
        qp.drawLine(self.__axis_mid, 0, self.__axis_mid, self.__height)

        main_scale_start = int(self.__axis_mid - 15)
        main_scale_end = int(self.__axis_mid + 15)
        sub_scale_start = int(self.__axis_mid - 5)
        sub_scale_end = int(self.__axis_mid + 5)

        for i in range(0, 12):
            y_main = int(self.__pixel_per_scale * i) - self.__paint_start_offset + TimeAxis.DEFAULT_MARGIN_PIXEL
            time_main = (self.__paint_start_scale + i) * self.__main_step
            qp.drawLine(main_scale_start, y_main, main_scale_end, y_main)
            qp.drawText(main_scale_end - 100, y_main, str(time_main))
            for j in range(0, 10):
                y_sub = int(y_main + self.__pixel_per_scale * j / 10)
                qp.drawLine(sub_scale_start, y_sub, sub_scale_end, y_sub)

    def paint_threads(self, qp: QPainter):
        for thread in self.__history_threads:
            thread.repaint(qp)

    def paint_real_time_tips(self, qp: QPainter):
        if not self.__enable_real_time_tips or self.__l_pressing:
            return

        qp.drawLine(0, self.__mouse_on_coordinate.y(), self.__width, self.__mouse_on_coordinate.y())
        qp.drawLine(self.__mouse_on_coordinate.x(), 0, self.__mouse_on_coordinate.x(), self.__height)

        tip_text = self.format_real_time_tip()

        fm = QFontMetrics(self.__tip_font)
        text_width = fm.width(tip_text)
        text_height = fm.height()
        tip_area = QRect(self.__mouse_on_coordinate, QSize(text_width, text_height))

        tip_area.setTop(tip_area.top() - fm.height())
        tip_area.setBottom(tip_area.bottom() - fm.height())
        if tip_area.right() > self.__axis_width:
            tip_area.setLeft(tip_area.left() - text_width)
            tip_area.setRight(tip_area.right() - text_width)

        qp.setFont(self.__tip_font)
        qp.setBrush(QColor(36, 169, 225))

        qp.drawRect(tip_area)
        qp.drawText(tip_area, Qt.AlignLeft, tip_text)

    # -------------------------------------------------- Calculation ---------------------------------------------------

    def index_from_point(self, point: QPoint) -> HistoricalRecord:
        for thread in self.__history_threads:
            index = thread.index_from_point(point)
            if index is not None:
                return index
        return None

    def calc_point_to_paint_start_offset(self, point):
        if self.__layout == TimeAxis.LAYOUT_HORIZON:
            return point.x() - TimeAxis.DEFAULT_MARGIN_PIXEL
        else:
            return point.y() - TimeAxis.DEFAULT_MARGIN_PIXEL

    def update_pixel_per_scale(self):
        self.__pixel_per_scale = self.__axis_length / self.__scale_per_page
        self.__pixel_per_scale = max(self.__pixel_per_scale, TimeAxis.MAIN_SCALE_MIN_PIXEL)

    def calc_paint_parameters(self):
        total_pixel_offset = self.__scroll + self.__offset

        self.__paint_since_scale = float(total_pixel_offset) / self.__pixel_per_scale
        self.__paint_until_scale = self.__paint_since_scale + self.__axis_length / self.__pixel_per_scale

        self.__paint_start_scale = math.floor(self.__paint_since_scale)
        self.__paint_start_offset = total_pixel_offset - self.__paint_start_scale * self.__pixel_per_scale

        for thread in self.__history_threads:
            thread.on_paint_scale_range_updated(self.__paint_since_scale * self.__main_step,
                                                self.__paint_until_scale * self.__main_step)

    def calc_paint_layout(self):
        self.__axis_mid = int(self.__axis_width * self.__axis_align_offset)

        threads_count = len(self.__history_threads)
        if threads_count == 0:
            return

        left_thread_count = int(threads_count * self.__axis_align_offset + 0.5)
        right_thread_count = threads_count - left_thread_count

        axis_left_margin = self.__axis_mid - self.__axis_space_w / 2
        axis_right_margin = self.__axis_mid + self.__axis_space_w / 2

        if left_thread_count > 0:
            left_thread_width = axis_left_margin / left_thread_count
        else:
            left_thread_width = 0

        if right_thread_count > 0:
            right_thread_width = (self.__axis_width - axis_right_margin) / right_thread_count
        else:
            right_thread_width = 0

        # Vertical -> Horizon : Left rotate
        for i in range(0, threads_count):
            thread = self.__history_threads[i]
            if self.__layout == TimeAxis.LAYOUT_HORIZON:
                pass
            else:
                top = TimeAxis.DEFAULT_MARGIN_PIXEL
                bottom = self.__axis_length - TimeAxis.DEFAULT_MARGIN_PIXEL
                if i < left_thread_count:
                    left = i * left_thread_width
                    area = QRect(QPoint(left, top), QPoint(left + left_thread_width, bottom))
                    thread.on_paint_canvas_size_update(area)
                else:
                    left = axis_right_margin + (i - left_thread_count) * right_thread_width
                    area = QRect(QPoint(left, top), QPoint(left + right_thread_width, bottom))
                    thread.on_paint_canvas_size_update(area)

    # ----------------------------------------------------- Scale ------------------------------------------------------

    def pixel_offset_to_scale_value(self, display_pixel_offset: int) -> float:
        delta_pixel_offset = display_pixel_offset + self.__paint_start_offset - self.DEFAULT_MARGIN_PIXEL
        delta_scale_offset = delta_pixel_offset / self.__pixel_per_scale
        return (self.__paint_start_scale + delta_scale_offset) * self.__main_step

    def auto_scale(self, since: float, until: float):
        since_rough = lower_rough(since)
        until_rough = upper_rough(until)
        delta = until_rough - since_rough
        delta_rough = upper_rough(delta)
        step_rough = delta_rough / 10

        step_index = 1
        while step_index < len(TimeAxis.STEP_LIST):
            if TimeAxis.STEP_LIST[step_index] < step_rough:
                break
            step_index += 1
        self.select_step_scale(step_index - 1)

        self.update_pixel_per_scale()
        self.__scroll = since_rough * self.__pixel_per_scale

    def select_step_scale(self, step_index: int):
        self.__step_selection = step_index
        self.__step_selection = max(self.__step_selection, 0)
        self.__step_selection = min(self.__step_selection, len(TimeAxis.STEP_LIST) - 1)

        self.__main_step = TimeAxis.STEP_LIST[self.__step_selection]
        self.__sub_step = self.__main_step / 10

        # abs_num = abs(num)
        # if abs_num >= 100:
        #     index_10 = math.log(abs_num, 10)
        #     round_index_10 = math.floor(index_10)
        #     scale = math.pow(10, round_index_10)
        #     delta = scale / 10
        # elif 10 < abs_num < 100:
        #     delta = 10
        # elif 1 < abs_num <= 10:
        #     delta = 1
        # else:
        #     if sign > 0:
        #         delta = 1
        #     else:
        #         delta = 0
        # return sign * delta * ratio

    # ------------------------------------------ Art ------------------------------------------

    def format_real_time_tip(self) -> str:
        tip_text = '(' + TimeParser.standard_time_to_str(self.__mouse_on_scale_value) + ')'
        if self.__mouse_on_index is not None:
            since = self.__mouse_on_index.since()
            until = self.__mouse_on_index.until()
            abstract_tags = self.__mouse_on_index.get_tags('abstract')
            abstract = abstract_tags[0] if len(abstract_tags) > 0 else ''
            abstract = abstract.strip()

            if len(abstract) > 0:
                tip_text += ' | '
                tip_text += abstract

            if since == until:
                tip_text += ' : [' + TimeParser.standard_time_to_str(since) + ']'
            else:
                tip_text += '(' + str(math.floor(self.__mouse_on_scale_value - since + 1)) + \
                            '/' + str(math.floor(until - since)) + ') : ['
                tip_text += TimeParser.standard_time_to_str(since) + \
                            ' - ' + TimeParser.standard_time_to_str(until) + ']'
        return tip_text

    # ------------------------------------- Real Time Tips ------------------------------------

    def on_pos_updated(self, pos: QPoint):
        if not self.__enable_real_time_tips:
            return
        if self.__mouse_on_coordinate != pos:
            self.__mouse_on_coordinate = pos
            self.__mouse_on_scale_value = self.pixel_offset_to_scale_value(pos.y())
            self.__mouse_on_index = self.index_from_point(pos)
            self.repaint()

    # ------------------------------- HistoryRecordEditor.Agent -------------------------------

    def on_apply(self):
        if self.__history_editor is None:
            print('Unexpected Error: History editor is None.')
            return

        records = self.__history_editor.get_history_editor().get_records()

        if records is None or len(records) == 0:
            return

        indexer = HistoricalRecordIndexer()
        indexer.index_records(records)
        indexes = indexer.get_indexes()

        # TODO: Maybe we should named it as update_*()
        self.__history_core.update_records(records)
        self.__history_core.update_indexes(indexes)

        self.__history_editor.on_apply()
        self.__history_editor.close()

        self.repaint()

    def on_cancel(self):
        if self.__history_editor is not None:
            self.__history_editor.close()
        else:
            print('Unexpected Error: History editor is None.')


# --------------------------------------------- class HistoryViewerDialog ----------------------------------------------

class HistoryViewerDialog(QDialog):
    def __init__(self):
        super(HistoryViewerDialog, self).__init__()

        self.time_axis = TimeAxis()
        layout = QVBoxLayout()
        layout.addWidget(self.time_axis)

        self.setLayout(layout)
        self.setWindowFlags(self.windowFlags() |
                            Qt.WindowMinMaxButtonsHint |
                            QtCore.Qt.WindowSystemMenuHint)

    def get_time_axis(self) -> TimeAxis:
        return self.time_axis


# ---------------------------------------------------- Test ------------------------------------------------------------

def test_upper_rough():
    assert math.isclose(upper_rough(10001), 20000)
    assert math.isclose(upper_rough(10000), 10000)
    assert math.isclose(upper_rough(9999), 10000)
    assert math.isclose(upper_rough(9001), 10000)
    assert math.isclose(upper_rough(8999),  9000)
    assert math.isclose(upper_rough(1.1), 2)
    # assert math.isclose(upper_rough(0.07), 0.07)

    assert math.isclose(upper_rough(-10001), -10000)
    assert math.isclose(upper_rough(-10000), -10000)
    assert math.isclose(upper_rough(-9999), -9000)
    assert math.isclose(upper_rough(-9001), -9000)
    assert math.isclose(upper_rough(-8999), -8000)
    assert math.isclose(upper_rough(-1.1), -1.0)
    # assert math.isclose(upper_rough(-0.07), 0.07)


def test_lower_rough():
    assert math.isclose(lower_rough(10001), 10000)
    assert math.isclose(lower_rough(10000), 10000)
    assert math.isclose(lower_rough(9999), 9000)
    assert math.isclose(lower_rough(9001), 9000)
    assert math.isclose(lower_rough(8999),  8000)
    assert math.isclose(lower_rough(1.1), 1.0)
    # assert math.isclose(lower_rough(0.07), 0.07)

    assert math.isclose(lower_rough(-10001), -20000)
    assert math.isclose(lower_rough(-10000), -10000)
    assert math.isclose(lower_rough(-9999), -10000)
    assert math.isclose(lower_rough(-9001), -10000)
    assert math.isclose(lower_rough(-8999), -9000)
    assert math.isclose(lower_rough(-1.1), -2.0)
    # assert math.isclose(upper_rough(-0.07), 0.07)


# ------------------------------------------------ File Entry : main() -------------------------------------------------

def main():
    test_upper_rough()
    test_lower_rough()

    app = QApplication(sys.argv)

    # Indexer
    indexer = HistoricalRecordIndexer()
    indexer.load_from_file('depot/history.index')
    indexer.print_indexes()

    # Threads
    thread = TimeAxis.Thread()
    thread.set_thread_color(THREAD_BACKGROUND_COLORS[0])
    thread.set_thread_event_indexes(indexer.get_indexes())

    # History
    history = History()
    history.update_indexes(indexer.get_indexes())

    # HistoryViewerDialog
    history_viewer = HistoryViewerDialog()
    history_viewer.get_time_axis().set_history_core(history)
    history_viewer.get_time_axis().add_history_thread(thread)
    history_viewer.exec()


# ----------------------------------------------------------------------------------------------------------------------

def exception_hook(type, value, tback):
    # log the exception here
    print('Exception hook triggered.')
    print(type)
    print(value)
    print(tback)
    # then call the default handler
    sys.__excepthook__(type, value, tback)


if __name__ == "__main__":
    sys.excepthook = exception_hook
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass


























