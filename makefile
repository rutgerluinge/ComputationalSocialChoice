##
# ComputationalSocialChoice programming assignment
#
# @file
# @version 0.1


install: reqs.txt
	pip install -r reqs.txt

dump_deps:
	pip-chill --no-version > reqs.txt

test: test_stv.py
	pytest

list_configs:
	python manip_main.py info list-configs

run_mayor_all:
	python manip_main.py run -d ./data/mayor.txt -s ALL

run_pliny_all:
	python manip_main.py run -d ./data/pliny.txt -s ALL

run_gui:
	streamlit run results_gui.py
# end
