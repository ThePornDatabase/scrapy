import sys

from pathlib import Path

import requests

from scrapy.http import HtmlResponse
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QStyleFactory, QTreeWidgetItem
from PySide2.QtCore import QFile, QIODevice

from tpdb.BaseSceneScraper import BaseSceneScraper


class GUI():
    request = None
    response = None
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
    }

    def __init__(self):
        app = QApplication(sys.argv)
        app.setStyle(QStyleFactory.create('Fusion'))

        ui_file_name = '%s.ui' % Path(__file__).stem
        ui_file = QFile(ui_file_name)
        if not ui_file.open(QIODevice.ReadOnly):
            print('Cannot open %s: %s' % (ui_file_name, ui_file.errorString()))
            sys.exit(-1)

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()
        if not self.window:
            print(loader.errorString())
            sys.exit(-1)

        self.connect()

        self.window.show()

        sys.exit(app.exec_())

    def connect(self):
        self.window.pushButton.pressed.connect(self.load)
        self.window.lineEdit_2.editingFinished.connect(self.get)

    def load(self):
        self.response = None

        url = self.window.lineEdit.text()
        try:
            self.request = requests.get(url)
        except:
            pass

        if self.request and self.request.ok:
            self.response = HtmlResponse(url=url, headers=self.headers, body=self.request.content)

            self.window.label.setText('<a href="{0}">{0}</a>'.format(url))
            self.window.plainTextEdit.setPlainText(self.request.text)

    def get(self):
        self.window.treeWidget.clear()

        selector = self.window.lineEdit_2.text().strip()
        if self.response:
            result = BaseSceneScraper.process_xpath(self, self.response, selector)

        if result:
            self.window.lineEdit_3.setText(result.get().strip())
            data = {k: v.strip() for k, v in enumerate(result.getall())}

            tree = QTreeWidgetItem()
            items = self.fill_item(tree, data)
            self.window.treeWidget.addTopLevelItems(items)
            self.window.treeWidget.expandAll()

    def fill_item(self, item, value):
        def new_item(parent, text, val=None):
            child = QTreeWidgetItem([text])
            self.fill_item(child, val)
            parent.addChild(child)

        if value is None:
            return None

        if isinstance(value, dict):
            for key, val in sorted(value.items()):
                new_item(item, str(key), val)
        elif isinstance(value, (list, tuple)):
            for val in value:
                text = (str(val) if not isinstance(val, (dict, list, tuple)) else '[%s]' % type(val).__name__)
                new_item(item, text, val)
        else:
            new_item(item, str(value))

        return [item]


if __name__ == '__main__':
    GUI()
