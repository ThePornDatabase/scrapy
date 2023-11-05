import sys

from pathlib import Path

from scrapy.http import TextResponse
from scrapy.utils import project
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QStyleFactory, QTreeWidgetItem
from PySide6.QtCore import QFile, QIODevice, QCoreApplication, Qt

from tpdb.helpers.http import Http
from tpdb.helpers.scrapy_dpath import DPathResponse
from tpdb.BaseScraper import BaseScraper


class GUI:
    request = None
    response = None
    headers = {}

    def __init__(self):
        QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
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
        self.setting()

        self.window.show()

        sys.exit(app.exec())

    def connect(self):
        self.window.pushButton.pressed.connect(self.load)
        self.window.lineEdit_2.editingFinished.connect(self.get)

    def setting(self):
        settings = project.get_project_settings()
        self.headers['User-Agent'] = settings.get('USER_AGENT', default='Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36')

    def get_response(self, content, request=None):
        url = request.url if request else ''
        response = TextResponse(url=url, headers=self.headers, body=content)
        response = DPathResponse(request, response)

        return response

    def load(self):
        self.request = None
        self.response = None

        url = self.window.lineEdit.text()
        if url:
            self.request = Http.get(url, headers=self.headers)

        if self.request is not None:
            self.response = self.get_response(self.request.content, self.request)

            self.window.label.setText('<a href="{0}">{0}</a>'.format(url))
            self.window.plainTextEdit.setPlainText(self.request.text)
        else:
            text = self.window.plainTextEdit.toPlainText().encode('UTF-8')
            if text:
                self.response = self.get_response(text)

                self.window.label.setText('From TextBox')

    def get(self):
        result = None
        self.window.treeWidget.clear()

        selector = self.window.lineEdit_2.text().strip()
        if self.response:
            result = BaseScraper.process_xpath(self.response, selector)

        if result:
            self.window.lineEdit_3.setText(result.get().strip())
            data = {k: v.strip() for k, v in enumerate(result.getall())}

            tree = QTreeWidgetItem()
            items = self.fill_item(tree, data)
            self.window.treeWidget.addTopLevelItems(items)
            self.window.treeWidget.expandAll()

    def fill_item(self, item, value):
        def new_item(parent, item_text, item_val=None):
            child = QTreeWidgetItem([item_text])
            self.fill_item(child, item_val)
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
