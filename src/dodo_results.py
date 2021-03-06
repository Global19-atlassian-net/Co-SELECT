from dodo_common import *

task_infos = []

for i, row in tfs.iterrows():
  tf = row['tf']
  bc = row['primer']
  motif = row['motif']
  family = row['family']
  dist = row['distance']
  accessions = row['accessions']
  task_infos.append(TaskInfo(tf, bc, family, accessions, [motif], cycles, [dist]))

tmp = tfs[['family', 'tf', 'primer', 'motif', 'distance']]
cross = pd.merge(tmp, tmp, on=tmp.assign(key_col=1)['key_col'])
cross = cross.loc[cross['family_x'] != cross['family_y']]

### UNCOMMENT THE FOLLOWING LINES IF TF PAIRS WITH SIMILAR MOTIFS TO BE EXCLUDED
#cross = cross.loc[~(((cross['family_x'] == 'homeodomain') & (cross['family_y'] == 'ETS'))
#                  | ((cross['family_y'] == 'homeodomain') & (cross['family_x'] == 'ETS')))]


def task_get_summary():
  """ Get summary information about enriched shapemers in the TF experiments"""
  for en_th in en_thresholds:
    for task in task_infos:
      for lflank, rflank in flank_configs:
        for shape_type in shapes:
          for levels_type in discrete_levels_type:
            shinfo = shape_info[levels_type][shape_type]
            shape_levels_str = shinfo.getLevelsStr()
            for cycle in task.cycles:
              for motif, dist in izip(task.motifs, task.distances):
                input_files = [top_data_dir +'/'+
                    task.tf_info.getContextedShapemerCountFile(cycle, motif,
                        dist, lflank, rflank, ctx, shape_type, shape_levels_str)
                    for ctx in contexts]
                resdir = '/'.join([top_results_dir, levels_type, en_th, 
                    task.family, task.tf, task.primer])
                file_fisher = '.'.join(['fisher', task.tf, task.primer,
                    shape_type, str(cycle), motif, str(lflank), str(rflank), 'csv'])
                output_file = '/'.join([resdir, file_fisher])
                prob_files = [getCycle0ProbFile(probability_dir, ctx, shape_type,
                    motif, dist, lflank, rflank, shape_levels_str) for ctx in contexts]
                yield {
                  'name'      : output_file,
                  'actions'   : ["results_scripts/get_summary.R "
                      "%s %s %d %s %s %d %d %d %s %s %s %s %s %s" % (task.tf,
                          task.primer, cycle, shape_type, motif, dist, lflank,
                          rflank, en_th, resdir, shape_levels_str, task.family,
                          top_data_dir, probability_dir)],
                  'file_dep'  : input_files + prob_files,
                  'targets'   : [output_file],
                  'clean'     : True,
                }

def task_get_cross_summary():
  """ Get summary information about enriched shapemers in the control experiments"""
  for i, row in cross.iterrows():
    tf1, tf2         = row[['tf_x', 'tf_y']]
    primer1, primer2 = row[['primer_x', 'primer_y']]
    motif1, motif2   = row[['motif_x', 'motif_y']]
    family1, family2 = row[['family_x', 'family_y']]
    dist1, dist2     = row[['distance_x', 'distance_y']]
    for cycle in cycles:
      for en_th in en_thresholds:
        for lflank, rflank in flank_configs:
          for shape_type in shapes:
            for levels_type in discrete_levels_type:
              shinfo = shape_info[levels_type][shape_type]
              shape_levels_str = shinfo.getLevelsStr()
              resdir = '%s/%s/%s/%s_%s' % (top_results_dir, levels_type, en_th,
                  min(family1, family2), max(family1, family2))
              info1 = TFInfo(tf1, primer1, family1)
              info2 = TFInfo(tf2, primer2, family2)
              input_files = [top_data_dir +'/'+
                  info1.getContextedShapemerCountFile(int(cycle), motif1, 
                      int(dist1), lflank, rflank, 'fg', shape_type, shape_levels_str)]
              input_files += [top_data_dir +'/'+
                  info2.getContextedShapemerCountFile(int(cycle), motif2,
                      int(dist2), lflank, rflank, 'bg', shape_type, shape_levels_str)]
              file_fisher = '.'.join(['fisher', tf1, primer1, motif1,
                  str(cycle), tf2, primer2, motif2, str(cycle), shape_type,
                  str(lflank), str(rflank), 'csv'])
              output_file = '/'.join([resdir, file_fisher])
              prob_files = [getCycle0ProbFile(probability_dir, 'fg', shape_type,
                  motif1, dist1, lflank, rflank, shape_levels_str)]
              prob_files += [getCycle0ProbFile(probability_dir, 'bg', shape_type,
                  motif2, dist2, lflank, rflank, shape_levels_str)]
              yield {
                'name'      : output_file,
                'actions'   : ["results_scripts/get_cross_summary.R "
                    "%s %s %s %s %d %d %s %s %s %s %d %d %s %d %d %s %s %s %s %s" % (
                        tf1, primer1, family1, motif1, dist1, cycle,
                        tf2, primer2, family2, motif2, dist2, cycle,
                        shape_type, lflank, rflank, en_th, resdir,
                        shape_levels_str, top_data_dir, probability_dir)],
                'file_dep'  : input_files + prob_files,
                'targets'   : [output_file],
                'clean'     : True,
              }

def task_same_enriched():
  """ Combine summary information about enriched shapemers in all TF experiments"""
  for en_th in en_thresholds:
    for cycle in cycles:
      for lflank, rflank in flank_configs:
        for shape_type in shapes:
          for levels_type in discrete_levels_type:
            inputs = ['/'.join([top_results_dir, levels_type, en_th, task.family,
                task.tf, task.primer, '.'.join(['enriched', task.tf, task.primer,
                    shape_type, str(cycle), motif, str(lflank), str(rflank), 'csv'])])
                for task in task_infos for motif, dist in izip(task.motifs, task.distances)]
            infos = [(task.tf, task.primer, task.family, task.tf, task.primer,
                task.family) for task in task_infos
                    for motif, dist in izip(task.motifs, task.distances)]
            target = '%s/%s/%s/denriched_%s.%s.%d.l%d.r%d.csv' % (top_results_dir,
                levels_type, en_th, 'same', shape_type, cycle, lflank, rflank)
            yield {
              'name'      : target,
              'actions'   : [(combine_data_frames, [inputs, infos, target])],
              'file_dep'  : inputs,
              'targets'   : [target],
              'clean'     : True,
            }


def task_same_fisher():
  """ Combine Fisher's test results for enriched shapemers in all TF experiments"""
  for en_th in en_thresholds:
    for cycle in cycles:
      for lflank, rflank in flank_configs:
        for shape_type in shapes:
          for levels_type in discrete_levels_type:
            inputs = ['/'.join([top_results_dir, levels_type, en_th, task.family,
                task.tf, task.primer, '.'.join(['fisher', task.tf, task.primer,
                    shape_type, str(cycle), motif, str(lflank), str(rflank), 'csv'])])
                for task in task_infos for motif, dist in izip(task.motifs, task.distances)]
            infos = [(task.tf, task.primer, task.family, task.tf, task.primer,
                task.family) for task in task_infos
                    for motif, dist in izip(task.motifs, task.distances)]
            target = '%s/%s/%s/dfisher_%s.%s.%d.l%d.r%d.csv' % (top_results_dir,
                levels_type, en_th, 'same', shape_type, cycle, lflank, rflank)
            yield {
              'name'      : target,
              'actions'   : [(combine_data_frames, [inputs, infos, target])],
              'file_dep'  : inputs,
              'targets'   : [target],
              'clean'     : True,
            }


def task_combine_same_fisher():
  """ Combine Fisher's test results for enriched shapemers in all TF experiments
  for all shapes and all enrichment thresholds"""
  for lflank, rflank in flank_configs:
    for levels_type in ['publish']:
      for cycle in [4]:
        df = pd.DataFrame(index = pd.MultiIndex.from_product([en_thresholds, shapes],
            names = ["en_th", "shape"]))
        df = df.reset_index()
        df['infile'] = df.apply(lambda x: '%s/%s/%s/dfisher_%s.%s.%d.l%d.r%d.csv' % (
            top_results_dir, levels_type, x["en_th"], 'same', x['shape'], cycle,
            lflank, rflank), axis='columns')
        outfile = "%s/%s/combined_fisher.%d.l%d.r%d.csv" % (top_results_dir,
            levels_type, cycle, lflank, rflank)
        yield {
          'name'      : outfile,
          'actions'   : [(combine_csvs, [df, outfile])],
          'file_dep'  : df['infile'].tolist(),
          'targets'   : [outfile],
          'clean'     : True,
        }

def task_cross_fisher():
  """ Combine Fisher's test results for enriched shapemers in all control experiments"""
  combinations = []
  for i, row in cross.iterrows():
    tf1, tf2         = row[['tf_x', 'tf_y']]
    primer1, primer2 = row[['primer_x', 'primer_y']]
    motif1, motif2   = row[['motif_x', 'motif_y']]
    family1, family2 = row[['family_x', 'family_y']]
    dist1, dist2     = row[['distance_x', 'distance_y']]
    resdir = '%s_%s' % (min(family1, family2), max(family1, family2))
    combinations.append((resdir, tf1, primer1, motif1, family1, dist1,
        tf2, primer2, motif2, family2, dist2))
  for en_th in en_thresholds:
    for cycle in cycles:
      for lflank, rflank in flank_configs:
        for shape_type in shapes:
          for levels_type in discrete_levels_type:
            inputs = ['/'.join([top_results_dir, levels_type, en_th, resdir,
                '.'.join(['fisher', tf1, primer1, motif1, str(cycle), tf2, primer2,
                    motif2, str(cycle), shape_type, str(lflank), str(rflank), 'csv'])])
                for resdir, tf1, primer1, motif1, family1, dist1, tf2, primer2, motif2, family2, dist2 in combinations]
            infos = [(tf1, primer1, family1, tf2, primer2, family2)
                for resdir, tf1, primer1, motif1, family1, dist1, tf2, primer2, motif2, family2, dist2 in combinations]
            target = '%s/%s/%s/dfisher_%s.%s.%d.l%d.r%d.csv' % (top_results_dir,
                levels_type, en_th, 'cross', shape_type, cycle, lflank, rflank)
            yield {
              'name'      : target,
              'actions'   : [(combine_data_frames, [inputs, infos, target])],
              'file_dep'  : inputs,
              'targets'   : [target],
              'clean'     : True,
            }

def task_compute_qvalue():
  """ Do multiple test correction of Fisher's test results"""
  for en_th in en_thresholds:
    for lflank, rflank in flank_configs:
      for cycle in cycles:
        for shape_type in shapes:
          for levels_type in discrete_levels_type:
            for family in ['bHLH', 'ETS', 'homeodomain']:
              for exp_type in ['same', 'cross']:
                infile = '%s/%s/%s/dfisher_%s.%s.%d.l%d.r%d.csv' % (
                    top_results_dir, levels_type, en_th, exp_type, shape_type,
                    cycle, lflank, rflank)
                outfile = '%s/%s/%s/dqvalue_%s.%s.%s.%d.l%d.r%d.csv' % (
                    top_results_dir, levels_type, en_th, exp_type, family,
                    shape_type, cycle, lflank, rflank)
                yield {
                  'name'      : outfile,
                  'actions'   : ["results_scripts/compute_qvalue.R %s %s %s %s" % (
                      shape_type, family, infile, outfile)],
                  'file_dep'  : [infile],
                  'targets'   : [outfile],
                  'clean'     : True,
                }


def task_combine_all_qvalues():
  """ Combine all multiple test corrected Fisher's test results in a single table"""
  for lflank, rflank in flank_configs:
    for cycle in cycles:
      infiles = ['%s/%s/%s/dqvalue_%s.%s.%s.%d.l%d.r%d.csv' % (top_results_dir,
          levels_type, en_th, exp_type, family, shape_type, cycle, lflank, rflank)
          for en_th in en_thresholds
            for shape_type in shapes
              for levels_type in discrete_levels_type
                for family in ['bHLH', 'ETS', 'homeodomain']
                  for exp_type in ['same', 'cross']]
      infos = [(en_th, shape_type, levels_type, family,
          'experiment' if (exp_type == 'same') else 'control')
          for en_th in en_thresholds
            for shape_type in shapes
              for levels_type in discrete_levels_type
                for family in ['bHLH', 'ETS', 'homeodomain']
                  for exp_type in ['same', 'cross']]
      outfile = '%s/dqvalue.%d.l%d.r%d.csv' % (top_results_dir, cycle, lflank, rflank)
      yield {
        'name'      : outfile,
        'actions'   : [(combine_qvalues, [infiles, infos, outfile])],
        'file_dep'  : infiles,
        'targets'   : [outfile],
        'clean'     : True,
      }

