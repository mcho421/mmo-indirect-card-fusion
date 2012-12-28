#!/usr/bin/env python

import sys
from collections import OrderedDict
from functools import partial
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import card_fusion
import ui_cardsynthesis

class CardFusionDlg(QDialog, ui_cardsynthesis.Ui_cardSynthesis):
    """docstring for CardFusionDlg"""
    def __init__(self, parent=None):
        super(CardFusionDlg, self).__init__(parent)
        self.setupUi(self)
        self.weaponLevelBox.selectAll()
        materialBoxes = [self.weaponNBox, self.weaponRBox, self.weaponRRBox,
                         self.weaponSBox, self.weaponSSBox, self.skillNBox,
                         self.skillRBox, self.skillRRBox, self.skillSBox,
                         self.skillSSBox]
        for box in materialBoxes:
            self.connect(box, SIGNAL("valueChanged(int)"), 
                partial(self.deselect_box, box=box), Qt.QueuedConnection)
            self.connect(box, SIGNAL("valueChanged(int)"), self.set_dirty)
        headers = self.recipeTable.horizontalHeader()
        # headers.setContextMenuPolicy(Qt.CustomContextMenu)
        # headers.customContextMenuRequested.connect(self.popup)
        headers.setMovable(True)
        self.ftype = None
        self.final_level = None
        self.final_ato = None
        self.N_count  = None
        self.R_count  = None
        self.RR_count = None
        self.S_count  = None
        self.SS_count = None
        self.dirty = True
    
    def popup(self, pos):
        for i in self.recipeTable.selectionModel().selection().indexes():
            print i.row(), i.column()
        menu = QMenu()
        quitAction = menu.addAction("Quit")
        hideAction = menu.addAction("Hide Column")
        action = menu.exec_(self.recipeTable.mapToGlobal(pos))
        if action == quitAction:
            qApp.quit()

    def deselect_box(self, value, box):
        box.lineEdit().deselect()

    def set_dirty(self):
        self.dirty = True
        self.fuseButton.setEnabled(False)
        # print "dirty"

    @pyqtSignature("int")
    def on_weaponLevelBox_valueChanged(self):
        self.set_dirty()

    @pyqtSignature("int")
    def on_skillLevelBox_valueChanged(self):
        self.set_dirty()

    @pyqtSignature("int")
    def on_weaponAtoBox_valueChanged(self):
        self.set_dirty()

    @pyqtSignature("int")
    def on_skillAtoBox_valueChanged(self):
        self.set_dirty()

    @pyqtSignature("double")
    def on_weaponExpRate_valueChanged(self):
        self.set_dirty()

    @pyqtSignature("double")
    def on_skillExpRate_valueChanged(self):
        self.set_dirty()

    @pyqtSignature("int")
    def on_weaponRarityBox_currentIndexChanged(self):
        self.set_dirty()

    @pyqtSignature("int")
    def on_skillRarityBox_currentIndexChanged(self):
        self.set_dirty()

    @pyqtSignature("int, int, int, int")
    def on_recipeTable_currentCellChanged(self, n_row, n_col, p_row, p_col):
        # print n_row, n_col
        try:
            final_level_tuple = self.recipeTable.item(n_row, 5).data(Qt.EditRole).toInt()
            final_ato_tuple = self.recipeTable.item(n_row, 6).data(Qt.EditRole).toInt()
            self.final_level = final_level_tuple[0]
            self.final_ato = final_ato_tuple[0]
            self.N_count  = self.recipeTable.item(n_row, 7).data(Qt.EditRole).toInt()[0]
            self.R_count  = self.recipeTable.item(n_row, 8).data(Qt.EditRole).toInt()[0]
            self.RR_count = self.recipeTable.item(n_row, 9).data(Qt.EditRole).toInt()[0]
            self.S_count  = self.recipeTable.item(n_row, 10).data(Qt.EditRole).toInt()[0]
            self.SS_count = self.recipeTable.item(n_row, 11).data(Qt.EditRole).toInt()[0]
            # print self.final_level, self.final_ato
            if self.dirty == False:
                self.fuseButton.setEnabled(True)
        except AttributeError:
            self.set_dirty()
            return

    @pyqtSignature("")
    def on_fuseButton_clicked(self):
        if self.ftype == "weapon":
            self.weaponLevelBox.setValue(self.final_level)
            self.weaponAtoBox.setValue(self.final_ato)
            self.weaponNBox.setValue(self.weaponNBox.value() - self.N_count)
            self.weaponRBox.setValue(self.weaponRBox.value() - self.R_count)
            self.weaponRRBox.setValue(self.weaponRRBox.value() - self.RR_count)
            self.weaponSBox.setValue(self.weaponSBox.value() - self.S_count)
            self.weaponSSBox.setValue(self.weaponSSBox.value() - self.SS_count)
        elif self.ftype == "skill":
            self.skillLevelBox.setValue(self.final_level)
            self.skillAtoBox.setValue(self.final_ato)
            self.skillNBox.setValue(self.skillNBox.value() - self.N_count)
            self.skillRBox.setValue(self.skillRBox.value() - self.R_count)
            self.skillRRBox.setValue(self.skillRRBox.value() - self.RR_count)
            self.skillSBox.setValue(self.skillSBox.value() - self.S_count)
            self.skillSSBox.setValue(self.skillSSBox.value() - self.SS_count)

    @pyqtSignature("")
    def on_weaponRecipeButton_clicked(self):
        self.generate_recipes(ftype="weapon")

    @pyqtSignature("")
    def on_skillRecipeButton_clicked(self):
        self.generate_recipes(ftype="skill")

    @pyqtSignature("")
    def on_weaponResetButton_clicked(self):
        self.clear_materials(ftype="weapon")

    @pyqtSignature("")
    def on_skillResetButton_clicked(self):
        self.clear_materials(ftype="skill")

    def clear_materials(self, ftype="weapon"):
        eval("self.{}NBox".format(ftype)).setValue(0)
        eval("self.{}RBox".format(ftype)).setValue(0)
        eval("self.{}RRBox".format(ftype)).setValue(0)
        eval("self.{}SBox".format(ftype)).setValue(0)
        eval("self.{}SSBox".format(ftype)).setValue(0)


    def generate_recipes(self, ftype="weapon"):
        def setNumeric(row, col, numeric):
            item = QTableWidgetItem()
            item.setData(Qt.EditRole, QVariant(numeric))
            self.recipeTable.setItem(row, col, item)

        base_card = card_fusion.Card(str(eval("self.{}RarityBox".format(ftype)).currentText()), 
                                     ato=eval("self.{}AtoBox".format(ftype)).value(),
                                     level=eval("self.{}LevelBox".format(ftype)).value())
        material_counter = {'N':eval("self.{}NBox".format(ftype)).value(), 
                            'R':eval("self.{}RBox".format(ftype)).value(), 
                            'RR':eval("self.{}RRBox".format(ftype)).value(), 
                            'S':eval("self.{}SBox".format(ftype)).value(), 
                            'SS':eval("self.{}SSBox".format(ftype)).value()}
        exp_rate = eval("self.{}ExpRate".format(ftype)).value()
        recipes = card_fusion.possible_fuses(base_card, material_counter, ftype=ftype, rate=exp_rate)
        self.recipeTable.clearContents()
        self.recipeTable.setSortingEnabled(False)
        self.recipeTable.setRowCount(len(recipes))
        for i, recipe in enumerate(recipes):
            exp_per_coin   = recipe['exp_per_coin']
            fodder_rarity  = recipe['fodder_rarity']
            fodder_level   = recipe['fodder_level']
            materials      = recipe['materials']
            exp_efficiency = recipe['exp_efficiency']
            exp_to_base    = recipe['exp_to_base']
            total_cost     = recipe['total_cost']
            final_level    = recipe['final_level']
            final_ato      = recipe['final_ato']
            fodder_counts  = recipe['fodder_counts']

            self.recipeTable.setItem(i, 0, QTableWidgetItem("{}({})".format(fodder_rarity, materials)))
            setNumeric(i, 1, exp_per_coin)
            setNumeric(i, 2, exp_efficiency)
            # self.recipeTable.setItem(i, 2, QTableWidgetItem("{:.2%}".format(exp_efficiency)))
            setNumeric(i, 3, exp_to_base)
            setNumeric(i, 4, total_cost)
            setNumeric(i, 5, final_level)
            setNumeric(i, 6, final_ato)
            setNumeric(i, 7, fodder_counts['N'])
            setNumeric(i, 8, fodder_counts['R'])
            setNumeric(i, 9, fodder_counts['RR'])
            setNumeric(i, 10, fodder_counts['S'])
            setNumeric(i, 11, fodder_counts['SS'])
        self.recipeTable.setSortingEnabled(True)
        self.ftype = ftype
        self.dirty = False


def main():
    app = QApplication(sys.argv)
    form = CardFusionDlg()
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()