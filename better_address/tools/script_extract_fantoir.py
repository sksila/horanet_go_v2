import os
import sys
import getopt
import logging
import tempfile
import zipfile
import shutil
import imp
import re
from time import time

COUNTRY_ID = 'base.fr'
PREFIX_COUNTRY_STATE_ID = 'state_fr_'
SCRIPT_FILENAME = os.path.basename(__file__)
CHUNK_SIZE = 100000
WAY_NATURE_CODES = [
    ('ACH', 'ANCIEN CHEMIN'),
    ('AER', 'AERODROME'),
    ('AERG', 'AEROGARE'),
    ('AGL', 'AGGLOMERATION'),
    ('AIRE', 'AIRE'),
    ('ALL', 'ALLEE'),
    ('ANGL', 'ANGLE'),
    ('ARC', 'ARCADE'),
    ('ART', 'ANCIENNE ROUTE'),
    ('AUT', 'AUTOROUTE'),
    ('AV', 'AVENUE'),
    ('BASE', 'BASE'),
    ('BD', 'BOULEVARD'),
    ('BER', 'BERGE'),
    ('BORD', 'BORD'),
    ('BRE', 'BARRIERE'),
    ('BRG', 'BOURG'),
    ('BRTL', 'BRETELLE'),
    ('BSN', 'BASSIN'),
    ('CAE', 'CARRIERA'),
    ('CALL', 'CALLE, CALLADA'),
    ('CAMI', 'CAMIN'),
    ('CAMP', 'CAMP'),
    ('CAN', 'CANAL'),
    ('CAR', 'CARREFOUR'),
    ('CARE', 'CARRIERE'),
    ('CASR', 'CASERNE'),
    ('CC', 'CHEMIN COMMUNAL'),
    ('CD', 'CHEMIN DEPARTEMENTAL'),
    ('CF', 'CHEMIN FORESTIER'),
    ('CHA', 'CHASSE'),
    ('CHE', 'CHEMIN'),
    ('CHEM', 'CHEMINEMENT'),
    ('CHL', 'CHALET'),
    ('CHP', 'CHAMP'),
    ('CHS', 'CHAUSSEE'),
    ('CHT', 'CHATEAU'),
    ('CHV', 'CHEMIN VICINAL'),
    ('CITE', 'CITE'),
    ('CIVE', 'COURSIVE'),
    ('CLOS', 'CLOS'),
    ('CLR', 'COULOIR'),
    ('COIN', 'COIN'),
    ('COL', 'COL'),
    ('COR', 'CORNICHE'),
    ('CORO', 'CORON'),
    ('COTE', 'COTE'),
    ('COUR', 'COUR'),
    ('CPG', 'CAMPING'),
    ('CR', 'CHEMIN RURAL'),
    ('CRS', 'COURS'),
    ('CRX', 'CROIX'),
    ('CTR', 'CONTOUR'),
    ('CTRE', 'CENTRE'),
    ('DARS', 'DARSE, DARCE'),
    ('DEVI', 'DEVIATION'),
    ('DIG', 'DIGUE'),
    ('DOM', 'DOMAINE'),
    ('DRA', 'DRAILLE'),
    ('DSC', 'DESCENTE'),
    ('ECA', 'ECART'),
    ('ECL', 'ECLUSE'),
    ('EMBR', 'EMBRANCHEMENT'),
    ('EMP', 'EMPLACEMENT'),
    ('ENC', 'ENCLOS'),
    ('ENV', 'ENCLAVE'),
    ('ESC', 'ESCALIER'),
    ('ESP', 'ESPLANADE'),
    ('ESPA', 'ESPACE'),
    ('ETNG', 'ETANG'),
    ('FD', 'FOND'),
    ('FG', 'FAUBOURG'),
    ('FON', 'FONTAINE'),
    ('FOR', 'FORET'),
    ('FORT', 'FORT'),
    ('FOS', 'FOSSE'),
    ('FRM', 'FERME'),
    ('GAL', 'GALERIE'),
    ('GARE', 'GARE'),
    ('GBD', 'GRAND BOULEVARD'),
    ('GPL', 'GRANDE PLACE'),
    ('GR', 'GRANDE RUE'),
    ('GREV', 'GREVE'),
    ('HAB', 'HABITATION'),
    ('HAM', 'HAMEAU'),
    ('HIP', 'HIPPODROME'),
    ('HLE', 'HALLE'),
    ('HLG', 'HALAGE'),
    ('HLM', 'HLM'),
    ('HTR', 'HAUTEUR'),
    ('ILE', 'ILE'),
    ('ILOT', 'ILOT'),
    ('IMP', 'IMPASSE'),
    ('JARD', 'JARDIN'),
    ('JTE', 'JETEE'),
    ('LAC', 'LAC'),
    ('LEVE', 'LEVEE'),
    ('LICE', 'LICES'),
    ('LIGN', 'LIGNE'),
    ('LOT', 'LOTISSEMENT'),
    ('MAIL', 'MAIL'),
    ('MAIS', 'MAISON'),
    ('MAR', 'MARCHE'),
    ('MARE', 'MARE'),
    ('MAS', 'MAS'),
    ('MNE', 'MORNE'),
    ('MRN', 'MARINA'),
    ('MTE', 'MONTEE'),
    ('NTE', 'NOUVELLE ROUTE'),
    ('PAE', 'PETITE AVENUE'),
    ('PARC', 'PARC'),
    ('PAS', 'PASSAGE'),
    ('PASS', 'PASSE'),
    ('PCH', 'PETIT CHEMIN'),
    ('PCHE', 'PORCHE'),
    ('PHAR', 'PHARE'),
    ('PIST', 'PISTE'),
    ('PKG', 'PARKING'),
    ('PL', 'PLACE'),
    ('PLA', 'PLACA'),
    ('PLAG', 'PLAGE'),
    ('PLAN', 'PLAN'),
    ('PLCI', 'PLACIS'),
    ('PLE', 'PASSERELLE'),
    ('PLN', 'PLAINE'),
    ('PLT', 'PLATEAU'),
    ('PNT', 'POINTE'),
    ('PONT', 'PONT'),
    ('PORQ', 'PORTIQUE'),
    ('PORT', 'PORT'),
    ('POST', 'POSTE'),
    ('POT', 'POTERNE'),
    ('PROM', 'PROMENADE'),
    ('PRT', 'PETITE ROUTE'),
    ('PRV', 'PARVIS'),
    ('PTA', 'PETITE ALLEE'),
    ('PTE', 'PORTE'),
    ('PTR', 'PETITE RUE'),
    ('PTTE', 'PLACETTE'),
    ('QUA', 'QUARTIER'),
    ('QUAI', 'QUAI'),
    ('RAC', 'RACCOURCI'),
    ('REM', 'REMPART'),
    ('RES', 'RESIDENCE'),
    ('RIVE', 'RIVE'),
    ('RLE', 'RUELLE'),
    ('ROC', 'ROCADE'),
    ('RPE', 'RAMPE'),
    ('RPT', 'ROND-POINT'),
    ('RTD', 'ROTONDE'),
    ('RTE', 'ROUTE'),
    ('RUE', 'RUE'),
    ('RUET', 'RUETTE'),
    ('RUIS', 'RUISSEAU'),
    ('RULT', 'RUELLETTE'),
    ('RVE', 'RAVINE'),
    ('SAS', 'SAS'),
    ('SEN', 'SENTIER, SENTE'),
    ('SQ', 'SQUARE'),
    ('STDE', 'STADE'),
    ('TER', 'TERRE'),
    ('TOUR', 'TOUR'),
    ('TPL', 'TERRE-PLEIN'),
    ('TRA', 'TRAVERSE'),
    ('TRAB', 'TRABOULE'),
    ('TRN', 'TERRAIN'),
    ('TRT', 'TERTRE'),
    ('TSSE', 'TERRASSE'),
    ('TUN', 'TUNNEL'),
    ('VAL', 'VAL'),
    ('VALL', 'VALLON, VALLEE'),
    ('VC', 'VOIE COMMUNALE'),
    ('VCHE', 'VIEUX CHEMIN'),
    ('VEN', 'VENELLE'),
    ('VGE', 'VILLAGE'),
    ('VIA', 'VIA'),
    ('VIAD', 'VIADUC'),
    ('VIL', 'VILLE'),
    ('VLA', 'VILLA'),
    ('VOIE', 'VOIE'),
    ('VOIR', 'VOIRIE'),
    ('VOUT', 'VOUTE'),
    ('VOY', 'VOYEUL'),
    ('VTE', 'VIEILLE ROUTE'),
    ('ZA', 'ZA'),
    ('ZAC', 'ZAC'),
    ('ZAD', 'ZAD'),
    ('ZI', 'ZI'),
    ('ZONE', 'ZONE'),
    ('ZUP', 'ZUP')
]

imp.reload(sys)
# sys.setdefaultencoding('utf-8') UTF-8 by default
logging.basicConfig(level=20)
_logger = logging.getLogger('Referencial')


def main(argv):
    input_fantoir_file = None
    input_postal_codes_file = None
    output_file = os.path.expanduser('~/fantoir-extracted-{}.zip'.format(int(time())))
    selected_states = list()

    try:
        opts, args = getopt.getopt(argv, "hf:p:s:o:c:d",
                                   ["help", "fantoir=", "postalcodes=", "states=", "output=", "chunk-size=", "debug"])
    except getopt.GetoptError:
        print("Bad command, type '-h' argument to get more informations.")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print("""
###############################
####### EXTRACT FANTOIR #######
#######  PYTHON MODULE  #######
###############################

#############
# ARGUMENTS #
#############

-f --fantoir (required)
Declare FANTOIR file location.

-p --postalcodes (required)
Declare postal codes file location.

-s --states
Declare french states to add to final archive. By default, all states are loaded.

-o --output
Declare output file location. If not set, file will be move to the home of current user.

-c --chunk-size
Define chunk size to explore FANTOIR file.

-d --debug
Define log level to DEBUG.

-h --help
Show help prompt.

###########
# EXAMPLE #
###########

python script_extract_fantoir.py -f \"/my/directory/FANTOIR0417.zip\" -z \"/my/direc" \
      "tory/postalcode.csv\" -o \"/my/directory/archive.zip\"

#############
# DOWNLOADS #
#############

Links to download files:
 - https://www.data.gouv.fr/fr/datasets/fichier-fantoir-des-voies-et-lieux-dits/
 - https://www.data.gouv.fr/fr/datasets/base-officielle-des-codes-postaux
              """)
            sys.exit()
        elif opt in ("-f", "--fantoir"):
            input_fantoir_file = os.path.abspath(arg)
            if not os.path.isfile(input_fantoir_file):
                print(("The file %s does not exist" % arg))
                sys.exit(2)
        elif opt in ('-p', '--postalcodes'):
            input_postal_codes_file = os.path.abspath(arg)
            if not os.path.isfile(input_postal_codes_file):
                print(("The file %s does not exist" % arg))
                sys.exit(2)
        elif opt in ('-s', '--states'):
            pattern = re.compile('(2a|2b|97[1-6]|[\d]{2}|[\d]{1}),?', re.IGNORECASE)
            selected_states = [str(state_id) if len(state_id) > 1 else str('0' + state_id) for state_id in
                               pattern.findall(arg)]
        elif opt in ('-o', '--output'):
            output_file = os.path.abspath(arg)
        elif opt in ('-c', '--chunk-size'):
            if int(arg) < 1:
                print(("Chunk size %s is not a good value, an integer greater than 0 is expected" % str(arg)))
                sys.exit(2)
            global CHUNK_SIZE
            CHUNK_SIZE = int(arg)
        elif opt in ('-d', '--debug'):
            _logger.setLevel(10)
    if not (input_fantoir_file and input_postal_codes_file):
        print("Missing argument. try --help")
        sys.exit(2)

    start_time = time()

    _logger.info("Selected states: %s" % ','.join(selected_states))

    _logger.info("Create temp directory...")
    tmp_dir = tempfile.mkdtemp()
    _logger.info("Temp directory %s created!" % str(tmp_dir))

    fantoir_filename, postal_codes_filename, output_filename = get_filenames(tmp_dir, output_file, input_fantoir_file,
                                                                             input_postal_codes_file)

    _logger.info("Create CSV files...")
    # output_zips_csv_file = os.path.join(tmp_dir, "zip.csv")
    output_cities_csv_file = os.path.join(tmp_dir, "city.csv")
    output_streets_csv_file = os.path.join(tmp_dir, "street.csv")
    output_street_numbers_csv_file = os.path.join(tmp_dir, "street_number.csv")
    # open(output_zips_csv_file, 'a').close()
    open(output_cities_csv_file, 'a').close()
    open(output_streets_csv_file, 'a').close()
    open(output_street_numbers_csv_file, 'a').close()
    _logger.info("CSV files created!")

    _logger.info("Fill CSV files...")
    zips_by_insee, zips_list = explode_zips_file(postal_codes_filename)
    fill_street_numbers_file(output_street_numbers_csv_file)
    # fill_zips_file(zips_list, output_zips_csv_file, selected_states)
    fill_cities_and_streets_files(fantoir_filename, zips_by_insee, output_cities_csv_file, output_streets_csv_file,
                                  selected_states)
    _logger.info("CSV files filled!")

    _logger.info("Archive CSV files...")
    zip_file = zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED)
    # zip_file.write(output_zips_csv_file, os.path.basename(output_zips_csv_file))
    zip_file.write(output_cities_csv_file, os.path.basename(output_cities_csv_file))
    zip_file.write(output_streets_csv_file, os.path.basename(output_streets_csv_file))
    zip_file.write(output_street_numbers_csv_file, os.path.basename(output_street_numbers_csv_file))
    zip_file.close()
    _logger.info("CSV files archived!")

    _logger.info("Complete in %s seconds!" % (time() - start_time))

    _logger.debug("Delete temp directory: %s" % str(tmp_dir))
    shutil.rmtree(tmp_dir)
    return True


def get_filenames(tmp_dir, output_file, input_fantoir_file, input_postal_codes_file):
    # Copy and extract files to temporary directories for process

    # Extract FANTOIR file
    try:
        temp_dir_fantoir = os.path.join(tmp_dir, "fantoir")
        if not os.path.exists(temp_dir_fantoir):
            os.makedirs(temp_dir_fantoir)
        _logger.debug('Temp directory %s created!' % str(temp_dir_fantoir))

        pyzip = zipfile.ZipFile(input_fantoir_file)
        pyzip.extractall(temp_dir_fantoir)
        _logger.debug("FANTOIR file extracted from archive: %s" % os.path.basename(input_fantoir_file))

        fileNumber = len(os.listdir(temp_dir_fantoir))
        if fileNumber == 0:
            raise Warning("No files found in zip")
        elif fileNumber > 1:
            _logger.warning("Multiple files are found in zip, we'll take the first one")

        fantoir_filename = os.path.join(temp_dir_fantoir, os.listdir(temp_dir_fantoir)[0])
        if not os.path.isfile(fantoir_filename):
            raise Warning("%s Is not a file" % fantoir_filename)

    except zipfile.BadZipfile as e:
        _logger.error(e)

    # Copy zip file
    temp_dir_postal_codes = os.path.join(tmp_dir, "postal_codes")
    if not os.path.exists(temp_dir_postal_codes):
        os.makedirs(temp_dir_postal_codes)
    _logger.debug('Temp directory %s created!' % str(temp_dir_postal_codes))

    _logger.debug("Copy zip file in temp directory: %s")
    postal_codes_filename = os.path.join(temp_dir_postal_codes, os.path.basename(input_postal_codes_file))
    shutil.copyfile(input_postal_codes_file, postal_codes_filename)
    if not os.path.isfile(postal_codes_filename):
        raise Warning("%s Is not a file" % postal_codes_filename)

    # Delete output file if already exists and force it to zip extension
    output_filename = (output_file + ".zip") if output_file[len(output_file) - 4:] != ".zip" else output_file
    _logger.debug("Delete output file if already exists")
    if os.path.basename(output_filename) != os.path.basename(SCRIPT_FILENAME) \
            and os.path.basename(output_filename) != os.path.basename(fantoir_filename) \
            and os.path.basename(output_filename) != os.path.basename(postal_codes_filename) \
            and os.path.isfile(output_filename):
        os.remove(output_filename)

    return fantoir_filename, postal_codes_filename, output_filename


def explode_zips_file(filename):
    zips_by_insee = dict()
    zips_list = list()

    with open(filename) as POSTAL_CODES:
        # Escape headers line
        POSTAL_CODES.readline()

        for POSTAL_CODES_LINE in POSTAL_CODES:
            fields = POSTAL_CODES_LINE.rstrip().split(';')
            insee_code = str(fields[0] if len(fields[0]) == 5 else '0' + fields[0])
            postal_code = str(fields[2] if len(fields[2]) == 5 else '0' + fields[2])

            new_list = zips_by_insee.get(insee_code) or list()
            new_list.append(postal_code)
            zips_by_insee[insee_code] = sorted(list(set(new_list)))

            zips_list.append(postal_code)

    return zips_by_insee, sorted(list(set(zips_list)))


def fill_street_numbers_file(csv):
    _logger.info('Fill street number CSV file...')
    with open(csv, 'w') as street_numbers_file:
        street_numbers_file.write("name\n")
        for x in range(1, 1001):
            street_numbers_file.write(str(x) + "\n")
            street_numbers_file.write(str(x) + " Bis\n")
            street_numbers_file.write(str(x) + " Ter\n")
    _logger.info('Street number CSV file filled!')


# def fill_zips_file(zips_list, csv_output, selected_states):
#     _logger.info('Fill zip CSV file...')
#     with open(csv_output, 'w') as output:
#         output.write("name;id\n")
#         for zip in zips_list:
#             if zip[0:2] in selected_states or zip[0:3] in selected_states:
#                 output.write(zip + ";zip_" + zip + "\n")
#     _logger.info('Zip CSV file filled!')


def fill_cities_and_streets_files(fantoir, zips, csv_cities, csv_streets, selected_states):
    _logger.info('Fill city and street CSV files...')
    with open(csv_cities, 'w') as cities_file, open(csv_streets, 'w') as streets_file:
        cities_file.write("country_id;country_state_id;name;code;zip_ids\n")
        streets_file.write("city_code;name;code\n")

        for chunk in get_data_fantoir_in_chunks(fantoir, selected_states):
            for data in chunk:
                if data['_type'] == 'd':
                    # Direction line
                    pass

                elif data['_type'] == 'c':
                    # Town line

                    country_state_id = \
                        PREFIX_COUNTRY_STATE_ID \
                        + data['code_departement'] \
                        + (data['code_direction'] if data['code_departement'] == '97' else '')
                    zip_ids = str(','.join(zips.get(data['code_insee']) or []))
                    cities_file.write(
                        COUNTRY_ID
                        + ";" + country_state_id
                        + ";" + data['libelle_commune']
                        + ";" + data['code_insee']
                        + ";" + zip_ids + "\n")

                elif data['_type'] == 'v':
                    # Way line
                    label = ''
                    for way_nature_code, way_nature_label in WAY_NATURE_CODES:
                        if data['code_nature_voie'].strip() == way_nature_code:
                            label += way_nature_label + ' '

                    label += data['libelle_voie']
                    streets_file.write(
                        data['code_insee'] + ";" + label + ";" + data['identifiant_voie'] + "\n")

                else:
                    _logger.warning("Unknown data type encountered!")

    _logger.info('City and street CSV files filled!')


def get_data_fantoir_in_chunks(file_path, selected_states):
    total_lines_number = 0
    with open(file_path, "r") as f:
        f.seek(0)
        for _ in f.readlines():
            total_lines_number += 1

    with open(file_path, "r") as f:
        f.seek(0)
        f.readline()
        total_lines_number -= 1
        lines_number = 0
        while True:
            chunk = list()
            for i in range(CHUNK_SIZE):
                line = str(f.readline())
                if line.strip() == '':
                    # Break if empty line (FANTOIR doesn't have empty line)
                    break
                if line[73] == ' ':
                    state_ok = False if len(selected_states) > 0 else True
                    for selected_state in selected_states:
                        if re.match('^' + selected_state, line):
                            state_ok = True

                    if state_ok:
                        chunk.append({
                            '_type': 'd' if line[3] == ' ' else ('c' if line[7] == ' ' else 'v'),
                            'code_insee': line[0:2] + line[3:6],
                            'code_departement': line[0:2].strip(),
                            'code_direction': line[2:3].strip(),
                            'code_commune': line[3:6].strip(),
                            'identifiant_voie': line[6:10].strip(),
                            'cle_rivoli': line[10:11].strip(),
                            'code_nature_voie': line[11:15],
                            'libelle_direction': line[11:41].strip(),
                            'libelle_commune': line[11:41].strip(),
                            'libelle_voie': line[15:41].strip(),
                            'type_commune': line[42:43].strip(),
                            'caractere_rur': line[45:46].strip(),
                            'caractere_population': line[49:50].strip(),
                            'population_reelle': line[52:59].strip().lstrip('0'),
                            'population_a_part': line[59:66].strip().lstrip('0'),
                            'population_fictive': line[66:73].strip().lstrip('0'),
                            'caractere_annulation': line[73:74].strip(),
                            'date_annulation': line[74:81].lstrip('0'),
                            'date_creation_article': line[81:88].lstrip('0'),
                            'code_identificant_majic_voie': line[103:108].strip(),
                            'type_voie': line[108:109].strip(),
                            'caractere_lieu_dit': line[109:110].strip(),
                            'dernier_mot_alphabetique_voie': line[112:120].strip(),
                        })
                lines_number += 1
            print(("FANTOIR: %s/%s" % (lines_number, total_lines_number)))
            if not chunk and lines_number >= total_lines_number:
                # Break if chunk not contains data
                break
            yield chunk


if __name__ == "__main__":
    main(sys.argv[1:])
