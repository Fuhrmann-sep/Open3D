import open3d as o3d
import numpy as np
import re
import os
import sys
from open3d_test import download_fountain_dataset


def get_file_list(path, extension=None):

    def sorted_alphanum(file_list_ordered):
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda key: [
            convert(c) for c in re.split('([0-9]+)', key)
        ]
        return sorted(file_list_ordered, key=alphanum_key)

    if extension is None:
        file_list = [
            path + f
            for f in os.listdir(path)
            if os.path.isfile(os.path.join(path, f))
        ]
    else:
        file_list = [
            path + f
            for f in os.listdir(path)
            if os.path.isfile(os.path.join(path, f)) and
            os.path.splitext(f)[1] == extension
        ]
    file_list = sorted_alphanum(file_list)
    return file_list


def test_color_map():
    """
    Hard-coded values are from the 0.12 release. We expect the values to match
    exactly when OMP_NUM_THREADS=1. If more threads are used, there could be
    some small numerical differences.
    """

    path = download_fountain_dataset()
    depth_image_path = get_file_list(os.path.join(path, "depth/"),
                                     extension=".png")
    color_image_path = get_file_list(os.path.join(path, "image/"),
                                     extension=".jpg")
    assert (len(depth_image_path) == len(color_image_path))

    rgbd_images = []
    for i in range(len(depth_image_path)):
        depth = o3d.io.read_image(os.path.join(depth_image_path[i]))
        color = o3d.io.read_image(os.path.join(color_image_path[i]))
        rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
            color, depth, convert_rgb_to_intensity=False)
        rgbd_images.append(rgbd_image)

    camera = o3d.io.read_pinhole_camera_trajectory(
        os.path.join(path, "scene/key.log"))
    mesh = o3d.io.read_triangle_mesh(
        os.path.join(path, "scene", "integrated.ply"))

    # Computes averaged color without optimization
    option = o3d.pipelines.color_map.ColorMapOptimizationOption()
    option.maximum_iteration = 0
    with o3d.utility.VerbosityContextManager(
            o3d.utility.VerbosityLevel.Info) as cm:
        o3d.pipelines.color_map.color_map_optimization(mesh, rgbd_images,
                                                       camera, option)
    vertex_mean = np.mean(np.asarray(mesh.vertex_colors), axis=0)
    extrinsic_mean = np.array([c.extrinsic for c in camera.parameters
                              ]).mean(axis=0)
    np.testing.assert_allclose(vertex_mean,
                               np.array([
                                   0.40322907,
                                   0.37276872,
                                   0.54375919,
                               ]),
                               rtol=1e-06)
    np.testing.assert_allclose(
        extrinsic_mean,
        np.array([
            [0.77003829, -0.10813595, 0.06467495, -0.56212008],
            [0.19100387, 0.86225833, -0.14664845, -0.81434887],
            [-0.05557141, 0.16504166, 0.82036438, 0.27867426],
            [0., 0., 0., 1.],
        ]),
        rtol=1e-06)

    # Rigid Optimization
    option.maximum_iteration = 10
    option.non_rigid_camera_coordinate = False
    with o3d.utility.VerbosityContextManager(
            o3d.utility.VerbosityLevel.Info) as cm:
        o3d.pipelines.color_map.color_map_optimization(mesh, rgbd_images,
                                                       camera, option)
    vertex_mean = np.mean(np.asarray(mesh.vertex_colors), axis=0)
    extrinsic_mean = np.array([c.extrinsic for c in camera.parameters
                              ]).mean(axis=0)
    np.testing.assert_allclose(vertex_mean,
                               np.array([
                                   0.40294861,
                                   0.37250299,
                                   0.54338467,
                               ]),
                               rtol=1e-06)
    np.testing.assert_allclose(
        extrinsic_mean,
        np.array([
            [0.7699379, -0.10768808, 0.06543989, -0.56320637],
            [0.19119488, 0.8619734, -0.14717332, -0.8137762],
            [-0.05608781, 0.16546427, 0.81995183, 0.27725451],
            [0., 0., 0., 1.],
        ]),
        rtol=1e-06)

    # Non-rigid Optimization
    option.maximum_iteration = 10
    option.non_rigid_camera_coordinate = True
    with o3d.utility.VerbosityContextManager(
            o3d.utility.VerbosityLevel.Info) as cm:
        o3d.pipelines.color_map.color_map_optimization(mesh, rgbd_images,
                                                       camera, option)
    vertex_mean = np.mean(np.asarray(mesh.vertex_colors), axis=0)
    extrinsic_mean = np.array([c.extrinsic for c in camera.parameters
                              ]).mean(axis=0)
    np.testing.assert_allclose(vertex_mean,
                               np.array([
                                   0.4028204,
                                   0.37237733,
                                   0.54322786,
                               ]),
                               rtol=1e-06)
    np.testing.assert_allclose(
        extrinsic_mean,
        np.array([
            [0.76967962, -0.10824218, 0.0674025, -0.56381652],
            [0.19129921, 0.86245618, -0.14634957, -0.81500831],
            [-0.05765316, 0.16483281, 0.82054672, 0.27526268],
            [0., 0., 0., 1.],
        ]),
        rtol=1e-06)
