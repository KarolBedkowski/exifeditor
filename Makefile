RESOURCE_DIR = data
COMPILED_DIR = exifeditor/gui

UI_FILES = $(wildcard ${RESOURCE_DIR}/*.ui)
RESOURCES = $(wildcard ${RESOURCE_DIR}/*.qrc)

PYUIC = pyuic4
PYRCC = pyrcc4

COMPILED_UI = $(UI_FILES:$(RESOURCE_DIR)/%.ui=$(COMPILED_DIR)/_ui_%.py)
COMPILED_RESOURCES = $(RESOURCES:$(RESOURCE_DIR)/%.qrc=$(COMPILED_DIR)/_%_rc.py)

all : resources 
	#ui

resources : $(COMPILED_RESOURCES)

ui : $(COMPILED_UI)

$(COMPILED_DIR)/_ui_%.py : $(RESOURCE_DIR)/%.ui
	$(PYUIC) $< -o $@

$(COMPILED_DIR)/_%_rc.py : $(RESOURCE_DIR)/%.qrc
	$(PYRCC) $< -o $@

clean_res :
	$(RM) $(COMPILED_UI) $(COMPILED_RESOURCES) $(COMPILED_UI:.py=.pyc) $(COMPILED_RESOURCES:.py=.pyc)
