from pathlib import Path

def create_dirs(filepath):
    cwd = Path.cwd()
    # print(f'[CURRENT DIRECTORY] {cwd}')
    # print(f'[DIRECTORY TO CREATE] {filepath}')
    # check if last dir/file indicated in path exist
    # if true, return false
    # else false, do nothing
    if filepath.exists():
        return False
    # check if filepath is an absolute path
    # if true, create new path relative to current directory
    # else false, do nothing
    if filepath.is_absolute():
        filepath = filepath.relative_to(cwd)
        # print(f'[RELATIVE TO CURRENT DIRECTORY] {filepath}')

    dir_list = []
    # seperate filepath to parts and loop through it
    path_parts = filepath.parts
    for part in path_parts:
        dir_list.append(part)
        new_path = Path('\\'.join(dir_list))

        # print(f'[EVALUATING] {new_path}')
        # if preceding path does not exists, create
        if not new_path.exists():
            if new_path.suffix == '':
                # create folder if path is a directory
                new_path.mkdir()
                print(f'[DIRECTORY CREATED] {new_path}')
            else:
                # create file if path is a file
                new_path.touch()
                # print(f'[FILE CREATED] {new_path}')
        # else:
        #     print(f'[PATH EXISTS] {part}')
    return True