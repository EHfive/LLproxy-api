import json

map_index = json.load(open('./datasource/maps_dict.min.json'))


def medley_fes(set_ids_list):
    weight = [0] * 9
    combo_weight = [0] * 9
    star_cnt = [0] * 9
    single_cnt = [0] * 9
    strip_cnt = [0] * 9
    pt_cnt = [0] * 9
    combo = 0
    combo_bynote = 0
    time_cnt = 0
    for set_id in set_ids_list:
        mapi = map_index[str(set_id)]

        notes = json.load(open('./datasource/SIFMaps/latest/' + mapi['notes_setting_asset']))
        t = 0
        for note in notes:
            p = 9 - note['position']
            combo += 1
            t = note['timing_sec']
            if note['effect'] == 1:
                single_cnt[p] += 1
                add = 1
            elif note['effect'] == 3:
                strip_cnt[p] += 1
                add = 1.25
            elif note['effect'] == 2:
                pt_cnt[p] += 1
                add = 1
            elif note['effect'] == 4:
                star_cnt[p] += 1
                star_cnt[p] += 1
                add = 1
            else:
                add = 1
            weight[p] += add
            combo_weight[p] += add * get_c(combo)
        time_cnt += t
    for k, v in enumerate(combo_weight):
        combo_weight[k] = round(v, 3)
        combo_bynote += combo_weight[k]

    return {
        'notes_weight': weight,
        'notes': combo,
        'combo_weight': combo_weight,
        'weighted_combo': round(combo_bynote, 3),
        'time_cnt': round(time_cnt),
        'cnt': {
            'pt': pt_cnt,
            'star': star_cnt,
            'single': single_cnt,
            'strip': strip_cnt
        }
    }


def get_c(combo):
    if combo > 800:
        return 1.35
    elif combo > 600:
        return 1.30
    elif combo > 400:
        return 1.25
    elif combo > 200:
        return 1.20
    elif combo > 100:
        return 1.15
    elif combo > 50:
        return 1.10
    elif combo > 0:
        return 1.00
    else:
        return 0


class MapNotFoundError(Exception):
    pass


class MapFormatWrong(Exception):
    pass


def merged_map(*setids):
    notes_merge = []
    for set_id in setids:
        try:
            mapi = map_index[str(set_id)]
            notes = json.load(open('./datasource/SIFMaps/latest/' + mapi['notes_setting_asset']))
        except KeyError:
            raise MapNotFoundError
        except FileNotFoundError:
            raise MapNotFoundError
        if notes_merge:
            try:
                t = notes_merge[-1]['timing_sec']
                d = notes[1]
            except IndexError:
                raise MapFormatWrong
            except KeyError:
                raise MapFormatWrong

            for k, note in enumerate(notes):
                notes[k]['timing_sec'] = round(note['timing_sec'] + t, 3)
        notes_merge.extend(notes)
    return notes_merge


if __name__ == '__main__':
    # sets = [78, 530, 374]
    # res = medley_fes(sets)
    sets_mf_best = [551, 391, 535]
    res = merged_map(*sets_mf_best)
    print(len(res))
    json.dump(res, open('mf_best.json', 'w'))
