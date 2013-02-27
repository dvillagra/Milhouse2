SHELL         = bash
MAKE          = make
MILHOUSE_HOME?= /home/mhsieh/WSGI_APACHE2/milhouse/dev
MILHOUSE_BASE = $(abspath $(MILHOUSE_HOME)/..)
ve_path       = virtualenv
thirdparty    = \
                numpy-1.6.1.tar.gz                                             \
#                simplejson-2.1.6.tar.gz                                        \
                Django-1.3.tar.gz                                              \
                Imaging-1.1.6.tar.gz                                           \
#                pymongo-1.11.tar.gz                                            \
#                hmarr-mongoengine-v0.4-0-g6998936.tar.gz                       \
                pyPdf-1.13.tar.gz                                              \
                ipython-0.10.2.tar.gz                                          \
                argparse-1.2.1.tar.gz                                          \
#                h5py-2.0.1.tar.gz                                              \
                pytz-2012c.tar.bz2
MONGODB_VER   = mongodb-linux-x86_64-2.0.1
# We might need these in the future:
#               docutils-0.8.1 \
#               Jinja2-2.6     \
#               Pygments-1.4   \
#               Sphinx-1.1.2
CHANGELIST   ?= $(shell p4 changes -m1 //depot/software/Milhouse/...\#have |   \
                            awk '{print $$2}')
BIOFX_DIR    ?= $(shell p4 fstat //depot/software/bioinformatics/... | head |  \
                            awk -F ' clientFile ' '/clientFile/{print $$2}' |  \
                            xargs dirname)
BUILD_DIR     = $(MILHOUSE_BASE)/build.archive/$(CHANGELIST)

# DEPENDENCIES
help: \
        /bin/cat
clean: \
        clean_ve
build_ve: \
        thirdparty/virtualenv.py
install_thirdparty: \
        build_ve
install_pbcore: \
        install_thirdparty \
        verify_pbcoredir
pipfreeze: \
        install_thirdparty
install_core: \
        install_thirdparty \
        install_pbcore \
        install_pbh5tools
install_pbh5tools: \
        install_pbcore \
        verify_pbh5toolsdir
mobilize_ve: \
        install_core
deploy_server: \
        verify_p4access \
        mobilize_ve
verify_pbcoredir: \
        verify_p4access \
        verify_biofxdir
verify_biofxdir: \
        verify_p4access
verify_pbh5toolsdir: \
        verify_p4access

# various check: normally use "test" to check
verify_p4access:
	@if [ "_$(CHANGELIST)" == "_" ]; then \
            p4 clients>&/dev/null; \
        fi
verify_pbcoredir:
	@test -d $(BIOFX_DIR)/lib/python/pbcore
verify_pbh5toolsdir:
	@test -d $(BIOFX_DIR)/tools/pbh5tools
verify_biofxdir:
	@if [ "_$(BIOFX_DIR)" == "_" ]; then \
            p4 client -o|grep 'depot/software/bioinformatics'>/dev/null; \
        fi
pipfreeze:
	@. $(ve_path)/bin/activate; pip freeze

# Rules
deploy_dev:
	@echo "[Info] This deploys everything for a Milhouse dev service"
	@echo "[Info] That means, service running at port 9883."
	@echo "[Info] deploying log folders."
	rsync -avx --delete --no-g deploy/folders/dev/ $(MILHOUSE_HOME)/
	@echo "[Info] deploying config files."
	cp deploy/conf_files/milhouse.conf $(MILHOUSE_HOME)/config/
	cp deploy/conf_files/mongodb.conf $(MILHOUSE_HOME)/config/
	cp deploy/conf_files/wsgi_site_dev.conf $(MILHOUSE_HOME)/config/httpd.conf
	@echo "[Info] deploying canonical scripts."
	rsync -avx --delete --no-g deploy/initd_scripts/ $(MILHOUSE_HOME)/init.d/
	cp deploy/run_scripts/runDjango.sh $(MILHOUSE_HOME)/init.d/
	@echo "[Info] deploying database data.(?)"
	@echo "rsync -avx --delete mp-f019:/mnt/secondary/Share/mhsieh/milhouse/dev/database/ $(MILHOUSE_HOME)/database/"
	@echo "[Info] deploying project data.(?)"
	@echo "rsync -avx --delete mp-f019:/mnt/secondary/Share/mhsieh/milhouse/dev/project/ $(MILHOUSE_HOME)/project/"
	@echo "[Info] deploying test folders."
	rsync -avx --delete --no-g deploy/test/ $(MILHOUSE_HOME)/test/
	@echo "[Info] deploying server link."
	cd $(MILHOUSE_HOME) && ln -s ../build_dev server

undeploy_server:
	@if [ ! -e "$(BUILD_DIR)" ]; then                                      \
            echo "[Info] nothing to be undeployed.";                           \
            exit 0;                                                            \
        fi
	rm -rf "$(BUILD_DIR)"
	rm -f "$(MILHOUSE_BASE)/build_dev"
	ln -s $(MILHOUSE_BASE)/`ls $(MILHOUSE_BASE)/|grep 'build\.......$$'|   \
                                sort|tail -1` "$(MILHOUSE_BASE)/build_dev"
	@echo "done"

#	This deploys a server build
deploy_server:
	@echo "[Info] Name collision check"
	@if [ -e "$(MILHOUSE_BASE)/build.$(CHANGELIST)" ]; then                \
            echo "[Info] skipping this server deployment, a build directory "; \
            echo "       with the same changelist exist.";                     \
            exit 0;                                                            \
        fi
	mkdir -p $(BUILD_DIR)
	@echo "[Info] deploying server scripts."
	rsync -ax --no-g scripts/ $(BUILD_DIR)/scripts/
	@echo "[Info] fixing scripts' shebang."
	@if [ ! -e /home/UNIXHOME/Share/R-installations/Rscript ]; then        \
            sed -i -e 's|#!/.*/R-installations/Rscript|#!/usr/bin/env Rscript|'\
            $(BUILD_DIR)/scripts/*.R; \
        fi
	@echo "[Info] deploying static files."
	rsync -ax --no-g static/ $(BUILD_DIR)/static/
	@echo "[Info] deploying django codes."
	rsync -ax --no-g --exclude doc --exclude Makefile                      \
            django_code/ $(BUILD_DIR)/django_code/
	@echo "[Info] deploying mongodb binaries."
	@if [ ! -e $(BUILD_DIR)/mongodb/bin/mongod ]; then                     \
            mkdir -p $(BUILD_DIR)/mongodb;                                     \
            tar zxf thirdparty/$(MONGODB_VER).tgz -C $(BUILD_DIR)/mongodb;     \
            cd $(BUILD_DIR)/mongodb/;                                          \
            ln -s $(MONGODB_VER)/bin bin;                                      \
        fi
	@echo "[Info] deploying python virtualenv."
	rsync -ax --no-g $(ve_path)/ $(BUILD_DIR)/$(ve_path)/
	@echo "[Info] fixing VIRTUAL_ENV value."
	sed -i -e "s|^ *VIRTUAL_ENV=\".*$$|VIRTUAL_ENV=\"$$(readlink -f        \
            $(BUILD_DIR)/virtualenv)\"|" $(BUILD_DIR)/virtualenv/bin/activate
	@echo "[Info] switching dev build."
	rm -f $(MILHOUSE_BASE)/build_dev &&                                    \
         cd $(MILHOUSE_BASE) &&                                                \
         ln -s build.archive/$(CHANGELIST) build_dev
	@echo "done"

mobilize_ve:
	python2.7 thirdparty/virtualenv.py --relocatable $(ve_path)
	@find $(ve_path) -type l                                               \
            | grep -v -e libpython2.7.so -e "$(ve_path)/local"                 \
            | xargs /bin/ls -l                                                 \
            | awk '/->/{print "rm "$$(NF-2)";cp -a "$$NF" "$$(NF-2)}'          \
            | $(SHELL)
	@echo "[Info] Fixing python shebang."
	@for myf in `find $(ve_path) -type f | grep -v libpython2.7.so |       \
            xargs grep $(ve_path) $(ve_path) | grep '#!' | awk -F ':'          \
            '{print $$1}'`; do                                                 \
            sed -i -e 's|^#\!.*python.*|#!/usr/bin/env python|' $$myf;         \
        done
	@if [ ! -e $(ve_path)/start_ve.sh ]; then                              \
            cp -a deploy/run_scripts/start_ve.sh $(ve_path)/;                  \
        fi;                                                                    \
        if [ ! -e $(ve_path)/stop_ve.sh ]; then                                \
            cp -a deploy/run_scripts/stop_ve.sh $(ve_path)/;                   \
        fi
	@echo "done"

install_pbcore:
	. $(ve_path)/bin/activate; \
        $(MAKE) -C $(BIOFX_DIR)/lib/python/pbcore install

install_pbh5tools:
	. $(ve_path)/bin/activate; \
        $(MAKE) -C $(BIOFX_DIR)/tools/pbh5tools install

install_core:
	. $(ve_path)/bin/activate; \
        $(MAKE) -C core

install_thirdparty:
	if [ ! -e /usr/include/hdf5.h ]; then                                 \
            echo "System libhdf5-*-dev is missing, installation might fail.";  \
        fi
	. $(ve_path)/bin/activate;                                            \
        for myp in $(thirdparty); do                                           \
            mypp="`echo $$myp|sed -e 's|\.tar\.gz||;s|\.tar\.bz2||;            \
                                      s|hmarr-mongoengine-v|mongoengine-|;     \
                                      s|-0-g6998936||;s|Imaging-|PIL-|;        \
                                      s|-|==|'`";                              \
            echo "[Info] Check if $${mypp} is installed in virtualenv.";       \
            if [ "_$$mypp" == "_" ]; then                                      \
                echo "[Error] something wrong in install_thirdparty";          \
                exit 1;                                                        \
            elif [ `pip freeze|grep $${mypp}|wc -l` -eq 0 ]; then              \
                pip install thirdparty/$$myp;                                  \
            fi;                                                                \
        done
	@echo "done"

build_ve:
	@if [ ! -e $(ve_path)/bin/activate ]; then                             \
            python2.7 thirdparty/virtualenv.py $(ve_path);                     \
        fi
	@if [ -e $(ve_path)/local ]; then                                      \
            rm -rf $(ve_path)/local;                                           \
        fi
	@echo "done"

clean_ve:
	rm -fr $(ve_path)

clean:
	$(MAKE) -C core clean
	$(MAKE) -C $(BIOFX_DIR)/lib/python/pbcore clean
	$(MAKE) -C $(BIOFX_DIR)/tools/pbh5tools clean
	rm -f thirdparty/virtualenv.pyc

super-clean:
	find * -type f | p4 -x - fstat 2>&1 > /dev/null                        \
           | awk -F ' - ' '/no such/{print $$1}'                               \
           | xargs rm -f
	@while [ `find * -type d -empty | wc -l` -gt 0 ]; do                   \
            find * -type d -empty | xargs rmdir;                               \
        done
	@echo "done"
#       Perforce Goodie

help:
	@echo 'Usage: '
	@echo '       make deploy_server'
	@echo '        or    env MILHOUSE_HOME=/tmp/dev make deploy_server'
	@echo '        or    make -e MILHOUSE_HOME=/tmp/dev deploy_server'
	@echo '       make undeploy_server'
	@echo '        (similar way to specify $$MILHOUSE_HOME)'
	@echo '       make clean'
	@echo '       make super-clean'
	@echo '       make help'

develop:
	rsync -ax --exclude doc --exclude Makefile django_code/ $(MILHOUSE_BASE)/build_dev/django_code/
	rsync -ax static/ $(MILHOUSE_BASE)/build_dev/static/
	rsync -ax scripts/ $(MILHOUSE_BASE)/build_dev/scripts/
	. $(ve_path)/bin/activate && $(MAKE) -C core
	rsync -ax virtualenv/ $(MILHOUSE_BASE)/build_dev/virtualenv 
