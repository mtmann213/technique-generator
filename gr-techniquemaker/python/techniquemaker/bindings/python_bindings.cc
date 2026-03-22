/*
 * Copyright 2020 Free Software Foundation, Inc.
 *
 * This file is part of GNU Radio
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 */

#include <pybind11/pybind11.h>

#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <numpy/arrayobject.h>

#include <gnuradio/techniquemaker/interdictor_cpp.h>

namespace py = pybind11;

void bind_interdictor_cpp(py::module& m)
{
    using interdictor_cpp = ::gr::techniquemaker::interdictor_cpp;

    py::class_<interdictor_cpp,
               gr::sync_block,
               gr::block,
               gr::basic_block,
               std::shared_ptr<interdictor_cpp>>(m, "interdictor_cpp")
        .def(py::init(&interdictor_cpp::make),
             py::arg("technique") = "Direct CW",
             py::arg("sample_rate_hz") = 2000000.0,
             py::arg("bandwidth_hz") = 100000.0,
             py::arg("reactive_threshold_db") = -45.0,
             py::arg("reactive_dwell_ms") = 400.0,
             py::arg("num_targets") = 1,
             py::arg("manual_mode") = false,
             py::arg("manual_freq") = 0.0,
             py::arg("jamming_enabled") = true,
             py::arg("adaptive_bw") = false,
             py::arg("preamble_sabotage") = false,
             py::arg("sabotage_duration_ms") = 20.0,
             py::arg("clock_pull_drift_hz_s") = 0.0,
             py::arg("stutter_enabled") = false,
             py::arg("stutter_clean_count") = 3,
             py::arg("stutter_burst_count") = 1,
             py::arg("stutter_randomize") = false,
             py::arg("frame_duration_ms") = 40.0,
             py::arg("output_mode") = "Continuous (Stream)")
        .def("set_technique", &interdictor_cpp::set_technique)
        .def("set_sample_rate_hz", &interdictor_cpp::set_sample_rate_hz)
        .def("set_bandwidth_hz", &interdictor_cpp::set_bandwidth_hz)
        .def("set_reactive_threshold_db", &interdictor_cpp::set_reactive_threshold_db)
        .def("set_reactive_dwell_ms", &interdictor_cpp::set_reactive_dwell_ms)
        .def("set_num_targets", &interdictor_cpp::set_num_targets)
        .def("set_manual_mode", &interdictor_cpp::set_manual_mode)
        .def("set_manual_freq", &interdictor_cpp::set_manual_freq)
        .def("set_jamming_enabled", &interdictor_cpp::set_jamming_enabled)
        .def("set_adaptive_bw", &interdictor_cpp::set_adaptive_bw)
        .def("set_preamble_sabotage", &interdictor_cpp::set_preamble_sabotage)
        .def("set_sabotage_duration_ms", &interdictor_cpp::set_sabotage_duration_ms)
        .def("set_clock_pull_drift_hz_s", &interdictor_cpp::set_clock_pull_drift_hz_s)
        .def("set_stutter_enabled", &interdictor_cpp::set_stutter_enabled)
        .def("set_stutter_clean_count", &interdictor_cpp::set_stutter_clean_count)
        .def("set_stutter_burst_count", &interdictor_cpp::set_stutter_burst_count)
        .def("set_stutter_randomize", &interdictor_cpp::set_stutter_randomize)
        .def("set_frame_duration_ms", &interdictor_cpp::set_frame_duration_ms)
        .def("set_output_mode", &interdictor_cpp::set_output_mode)
        .def("set_sticky_denial", &interdictor_cpp::set_sticky_denial)
        .def("set_look_through_ms", &interdictor_cpp::set_look_through_ms)
        .def("set_jam_cycle_ms", &interdictor_cpp::set_jam_cycle_ms)
        .def("clear_persistent_targets", &interdictor_cpp::clear_persistent_targets);
}

// We need this hack because import_array() returns NULL
// for newer Python versions.
// This function is also necessary because it ensures access to the C API
// and removes a warning.
void* init_numpy()
{
    import_array();
    return NULL;
}

PYBIND11_MODULE(techniquemaker_python, m)
{
    // Initialize the numpy C API
    // (otherwise we will see segmentation faults)
    init_numpy();

    // Allow access to base block methods
    py::module::import("gnuradio.gr");

    bind_interdictor_cpp(m);
}
