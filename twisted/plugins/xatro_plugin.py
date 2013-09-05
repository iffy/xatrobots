from twisted.application.service import ServiceMaker

serviceMaker = ServiceMaker('xatro', 'xatro.service', 'xatrobots server',
                            'xatro')