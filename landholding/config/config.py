# -*- coding: utf-8 -*-
FILE_TYPE_BATI = 'BATI'
FILE_TYPE_PROP = 'PROP'

FILE_MODEL_BATI = 'landholding.bati'
FILE_MODEL_OWNER = 'landholding.prop'
FILE_MODEL_COMM_ACCOUNT = 'landholding.communal.account'
FILE_MODEL_COMM_ACCOUNT_LINE = 'communal.account.line'

FILE_TYPES = [FILE_TYPE_BATI,
              FILE_TYPE_PROP]

FILE_MODELS = [FILE_MODEL_COMM_ACCOUNT,
               FILE_MODEL_BATI,
               FILE_MODEL_OWNER,
               FILE_MODEL_COMM_ACCOUNT_LINE]

FILE_MODEL_FILE_TYPE = dict()
FILE_MODEL_FILE_TYPE[FILE_MODEL_COMM_ACCOUNT] = FILE_TYPE_BATI
FILE_MODEL_FILE_TYPE[FILE_MODEL_BATI] = FILE_TYPE_BATI
FILE_MODEL_FILE_TYPE[FILE_MODEL_OWNER] = FILE_TYPE_PROP
FILE_MODEL_FILE_TYPE[FILE_MODEL_COMM_ACCOUNT_LINE] = FILE_TYPE_PROP

FILE_ARTICLE_POSITION = dict()
FILE_ARTICLE_POSITION[FILE_TYPE_BATI] = (31, 2)
FILE_ARTICLE_POSITION[FILE_TYPE_PROP] = ()

REQUIRED_DATA = dict()
REQUIRED_DATA[FILE_MODEL_BATI] = [('unique_id', ('00', '10'), 7, 10),                     # INVAR on all articles
                                  ('state_code', ('00'), 1, 2),                           # CCODEP
                                  ('city_insee_code', ('00'), 4, 3),                      # CCOCOM
                                  ('batiment_letter', ('00'), 46, 2),                     # DNUBAT
                                  ('entree_number', ('00'), 48, 2),                       # DESC
                                  ('floor_level', ('00'), 50, 2),                         # DNIV
                                  ('door_number', ('00'), 52, 5),                         # DNIV
                                  ('street_number', ('00'), 67, 4),                       # DNVOIRI
                                  ('repetition_code', ('00'), 71, 1),                     # DINDIC
                                  ('street_rivoli_code', ('00'), 57, 4),                  # CCORIV
                                  ('communal_account', ('10'), 38, 6),                    # DNUPRO
                                  ('local_type', ('10'), 60, 1),                          # DTELOC
                                  ]
REQUIRED_DATA[FILE_MODEL_OWNER] = [('unique_id', ('00'), 1, 14),                          # Indicatif
                                   ('majic_person_number', ('00'), 19, 6),                # DNUPER
                                   ('denomination', ('00'), 57, 60),                      # DDENOM
                                   ('address_line_1', ('00'), 121, 30),                   # DLIGN1
                                   ('address_line_2', ('00'), 151, 36),                   # DLIGN2
                                   ('address_line_3', ('00'), 187, 30),                   # DLIGN3
                                   ('address_line_4', ('00'), 217, 32),                   # DLIGN4
                                   ('title', ('00'), 287, 3),                             # DQUALP
                                   ('lastname', ('00'), 538, 60),                         # DNOMUS
                                   ('firstname', ('00'), 598, 40),                        # DPRNUS
                                   ('siren_number', ('00'), 467, 9),                      # DSIREN
                                   ]
REQUIRED_DATA[FILE_MODEL_COMM_ACCOUNT_LINE] = [('unique_id', ('00'), 1, 14),              # Indicatif
                                               ('state_code', ('00'), 1, 2),              # CCODEP
                                               ('city_insee_code', ('00'), 4, 3),         # CCOCOM
                                               ('communal_account', ('00'), 7, 6),        # DNUPRO
                                               ('partial_label_number', ('00'), 13, 2),   # DNULP
                                               ('majic_person_number', ('00'), 19, 6),    # DNUPER
                                               ('real_part_right_code', ('00'), 25, 1),   # CCODRO
                                               ]
REQUIRED_DATA[FILE_MODEL_COMM_ACCOUNT] = [('unique_id', ('00', '10'), 7, 10),             # INVAR on all articles
                                          ('communal_account', ('10'), 38, 6),            # DNUPRO
                                          ('state_code', ('00'), 1, 2),                   # CCODEP
                                          ('city_insee_code', ('00'), 4, 3),              # CCOCOM
                                          ]
