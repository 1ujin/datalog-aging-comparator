#!/usr/bin/env python
# -*- encoding:utf-8 -*-
"""
@Author : 卢晋
@File   : movablepushbutton.py
@Time   : 2023年05月11日
@Desc   : 可移动按钮
"""

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtCore import Qt

class MovablePushButton(QPushButton):

    def mousePressEvent(self, event):
        self.__mousePressPos = None
        self.__mouseMovePos = None
        if event.button() == Qt.LeftButton:
            self.__mousePressPos = event.globalPos()
            self.__mouseMovePos = event.globalPos()

        super(MovablePushButton, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            # adjust offset from clicked point to origin of widget
            currPos = self.mapToGlobal(self.pos())
            globalPos = event.globalPos()
            diff = globalPos - self.__mouseMovePos
            if diff.manhattanLength() < 20:
                event.ignore()
                return
            newPos = self.mapFromGlobal(currPos + diff)
            if self.parent():
                right = self.parent().geometry().width()
                bottom = self.parent().geometry().height()
                
                if newPos.x() < 0:
                    newPos.setX(0)
                elif newPos.x() > right - self.width():
                    newPos.setX(right - self.width())
                
                if newPos.y() < 0:
                    newPos.setY(0)
                elif newPos.y() > bottom - self.height():
                    newPos.setY(bottom - self.height())
                
                self.move(newPos)
            self.__mouseMovePos = globalPos

        super(MovablePushButton, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.__mousePressPos is not None:
            moved = event.globalPos() - self.__mousePressPos 
            if moved.manhattanLength() > 3:
                event.ignore()
                self.setDown(False)
                return

        super(MovablePushButton, self).mouseReleaseEvent(event)

def clicked():
    print("click as normal!")

if __name__ == "__main__":
    app = QApplication([])
    w = QWidget()
    w.resize(800,600)

    button = MovablePushButton("Drag", w)
    button.clicked.connect(clicked)

    w.show()
    app.exec_()