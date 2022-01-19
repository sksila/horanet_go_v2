# -*- coding: utf-8 -*-

[ALPHA, BETA, RELEASE_CANDIDATE, FINAL] = ['alpha', 'beta', 'candidate', 'final']
RELEASE_LEVELS_DISPLAY = {ALPHA: ALPHA,
                          BETA: BETA,
                          RELEASE_CANDIDATE: 'rc',
                          FINAL: ''}

# version_info format: (MAJOR, MINOR, MICRO, RELEASE_LEVEL, SERIAL)
# inspired by Python's own sys.version_info, in order to be
# properly comparable using normal operators, for example:
#  (6,1,0,'beta',0) < (6,1,0,'candidate',1) < (6,1,0,'candidate',2)
#  (6,1,0,'candidate',2) < (6,1,0,'final',0) < (6,1,2,'final',0)
version_info = (10, 3, 0, RELEASE_CANDIDATE, 0, ' 2018-12-21')
__version__ = '.'.join(map(str, version_info[:3])) + \
              RELEASE_LEVELS_DISPLAY[version_info[3]] + \
              str(version_info[4] or '') + \
              version_info[5]
