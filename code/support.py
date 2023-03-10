import pygame as pg
from os import walk

def import_folder(path):
    surface_list = []

    for folder, sub, file in walk(path):
        for img in file:
            full_path = path + '/' + img
            img_surf =  pg.image.load(full_path).convert_alpha()
            surface_list.append(img_surf)
    
    return surface_list

def import_folder_dict(path):
    surface_dict = {}

    for folder, sub, file in walk(path):
        for img in file:
            full_path = path + '/' + img
            img_surf =  pg.image.load(full_path).convert_alpha()
            surface_dict[img.split('.')[0]] = img_surf
    
    return surface_dict