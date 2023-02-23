$(document).ready(function () {
    var patient_select = document.getElementById('patient_select');
    var night_select = document.getElementById('night_select');
    var device_select = document.getElementById('device_select');
    var multi_night_device_select = document.getElementById('m_device_select');
    var narcolepsy_device_select = document.getElementById('n_device_select');
    var selected_device;
    var m_selected_device;
    var n_selected_device;
    var patient_options;
    var night_options;
    var selected_night;
    var selected_username;
    var selected_patient;

    const picker = new Litepicker({
        element: document.getElementById('multi_night_select'),
        singleMode: false,
        allowRepick: true
    });

    const n_picker = new Litepicker({
        element: document.getElementById('narcolepsy_night_select'),
        singleMode: false,
        allowRepick: true
    });

    get_patients_dropdown();
    $('.patient_result').hide();
    $('.recording_details').hide();
    $('.multi_recording_details').hide();
    $('.patient_multi_night_result').hide();

    function get_patients_dropdown() {
        $('.loading').show();
        clear_err_message();
        clear_recording_details_times();
        $('.patient_result').hide();
        $.ajax({
            type: "GET",
            url: "/patient_options",
            success: function (data) {
                patient_options = data.patients_option;
                selected_patient = patient_options[0].value;
                update_patient_dropdown(patient_options, selected_patient);
                fetch_patient_details(selected_patient);
                fetch_patient_question_ans(selected_patient);
                $('.loading').hide();

            },
            error: function (error) {
                if (error?.responseJSON?.data?.login_required) {
                    location.href = "/";
                    localStorage.setItem("SESSION_EXP", true);
                }
                show_err_message('night_option');
                $('.loading').hide();
            }
        })

    }

    function get_nights_dropdown(selected_patient, selected_device) {
        $('.loading').show();
        clear_err_message();
        $('.recording_details').hide();
        $('.patient_result').hide();
        $.ajax({
            type: "GET",
            url: "/patient_night_options",
            data: {
                selected_patient: selected_patient,
                selected_device: selected_device,
            },
            success: function (data) {
                update_night_dropdown(data);
                $('.loading').hide();

            },
            error: function (error) {
                if (error?.responseJSON?.data?.login_required) {
                    location.href = "/";
                    localStorage.setItem("SESSION_EXP", true);
                }
                show_err_message('night_option');
                $('.loading').hide();
            }
        })

    }


    function get_multi_nights_dropdown(selected_patient, selected_device) {
        $('.m_loading').show();
        $('.multi_recording_details').hide();
        $('.patient_multi_night_result').hide();
        $.ajax({
            type: "GET",
            url: "/patient_night_options",
            data: {
                selected_patient: selected_patient,
                selected_device: selected_device,
            },
            success: function (data) {
                highlight_multi_night_option(data);
                $('.m_loading').hide();

            },
            error: function (error) {
                if (error?.responseJSON?.data?.login_required) {
                    location.href = "/";
                    localStorage.setItem("SESSION_EXP", true);
                }
                show_err_message('night_option');
                $('.m_loading').hide();
            }
        })

    }


    function update_night_dropdown(dropdown_options) {
        var night_options = dropdown_options;
        $('#night_select').empty();
        night_options = dropdown_options.sort(function (a, b) {
            return new Date(a.value.split('/')[1]) - new Date(b.value.split('/')[1]);
        }).reverse();
        $(night_select).append('<option id=' + 0 + ' value=' + 0 + '>' + "Select Night ..." + '</option>');
        for (var i = 0; i < night_options.length; i++) {
            $(night_select).append('<option id=' + night_options[i].value + ' value=' + night_options[i].value + '>' + night_options[i].label + '</option>');
        }
        $('#night_select').niceSelect('update');

    }

    function highlight_multi_night_option(data) {
        var night_options = data;
        var highlighted_days = night_options.map(x => new Date(x['label']));
        picker.setHighlightedDays(highlighted_days);
    }

    function highlight_narcolepsy_option(data) {
        var night_options = data;
        var highlighted_days = night_options.map(x => new Date(x['label']));
        picker.setHighlightedDays(highlighted_days);
    }

    function get_recording_device_name(selected_device) {
        if (selected_device == 'fitbit') return "Fitbit Watch";
        if (selected_device == 'apple') return "Apple Watch";
        if (selected_device == 'uuid') return "Apple Watch";
    }

    function update_recording_details_times(rec_detail) {
        $('#recording_start_date').text(rec_detail.rec_start);
        $('#recording_end_date').text(rec_detail.rec_end);
        $('#recording_quality').text(rec_detail.quality);
        $('#recording_device').text(get_recording_device_name(selected_device));
        $('#recording_device_image').attr("src", '/static/images/' + selected_device + '.png');
        var date = date = new Date(rec_detail.rec_start);
        $('#recording_date').text(date.getDate());
        $('#recording_month').text(date.toLocaleString('default', {month: 'short'}));
        $('#recording_year').text(date.getFullYear());
    }

    function update_multi_night_recording_times(date_range) {
        var date_range_arr = date_range.split(" - ");
        $('#multi_night_recording_start_date').text(date_range_arr[0]);
        $('#multi_night_recording_end_date').text(date_range_arr[1]);
        $('#multi_night_recording_device').text(get_recording_device_name(m_selected_device));
        $('#multi_recording_device_image').attr("src", '/static/images/' + m_selected_device + '.png');
    }

    function clear_recording_details_times() {
        $('#recording_start_date').text("")
        $('#recording_end_date').text("")
        $('#recording_quality').text("")
        $('#recording_device').text("");
    }

    function clear_multi_night_recording_times() {
        $('#multi_night_recording_start_date').text("");
        $('#multi_night_recording_end_date').text("");
        $('#multi_night_recording_device').text("");
    }

    function update_patient_dropdown(dropdown_options, selected_option) {
        var patient_options = dropdown_options;
        for (var i = 0; i < patient_options.length; i++) {
            $(patient_select).append('<option id=' + patient_options[i].value + ' value=' + patient_options[i].value + '>' + patient_options[i].label.split('.').join(" ") + '</option>');

            if (patient_options[i].value == selected_option) {
                $('#patient_select').val(patient_options[i].value);
            }
        }
        $('#patient_select').niceSelect('update');
    }

    function fetch_patient_data(selected_patient, selected_device, selected_night) {
        $('.patient_result').hide();
        $('.recording_details').hide();
        $('.multi_recording_details').hide();
        clear_err_message();
        clear_recording_details_times();
        $('.loading').show();

        $.ajax({
            type: "GET",
            url: "/get_patient_data",
            data: {
                selected_patient: selected_patient,
                selected_device: selected_device,
                selected_night: selected_night,
            },
            success: function (data) {
                var hypnodensity_data = JSON.parse(data.hypnodensity_graphJSON);
                var hypnogram_data = JSON.parse(data.hypnogram_graphJSON);
                var stages_duration_data = JSON.parse(data.pie_stages_duration_graphJSON);
                //   var psg_fig_data = JSON.parse(data.psg_fig_graphJSON);
                var hr_fig_data = JSON.parse(data.hr_fig_graphJSON);
                var hrv_fig_data = JSON.parse(data.hrv_fig_graphJSON);
                var activity_fig_data = JSON.parse(data.activity_fig_graphJSON);
                //var awakeing_fig_data = JSON.parse(data.awakeing_fig_graphJSON);

                update_summary_table(JSON.parse(data.sleep_metrics_data));
                update_recording_details_times(data.rec_details);
                $('.recording_details').show();
                Plotly.newPlot(
                    "hypnodensity",
                    hypnodensity_data.data,
                    hypnodensity_data.layout
                );
                Plotly.newPlot("hypnogram", hypnogram_data.data, hypnogram_data.layout);
                //   Plotly.newPlot("sleep_stages", stages_duration_data.data, stages_duration_data.layout);
                //  Plotly.newPlot("awakening_graph", awakeing_fig_data.data, awakeing_fig_data.layout);
                Plotly.newPlot("hr_graph", hr_fig_data.data, hr_fig_data.layout);
                Plotly.newPlot("hrv_graph", hrv_fig_data.data, hrv_fig_data.layout);
                Plotly.newPlot("activity_graph", activity_fig_data.data, activity_fig_data.layout);
                resize_graphs();
                $('.loading').hide();
                $('.patient_result').show();
            },
            error: function (error) {
                if (error?.responseJSON?.data?.login_required) {
                    location.href = "/";
                    localStorage.setItem("SESSION_EXP", true);
                }
                show_err_message('patient_data');
                $('.loading').hide();
                $('.patient_result').hide();
            }
        });
    }

    function resize_graphs() {
        var d3 = Plotly.d3;
        gd3 = d3.selectAll('.graph_area')[0];
        $.each(gd3, function (index, elm) {
            Plotly.Plots.resize(elm);
        });
    }

    function fetch_patient_multi_night_data(selected_patient, selected_device, start_date, end_date) {
        $('.m_loading').show();
        $('.patient_multi_night_result').hide();
        $('.multi_recording_details').hide();
        hide_multi_night_err_message();
        clear_multi_night_recording_times()

        $.ajax({
            type: "GET",
            url: "/get_patient_multi_night_data",
            data: {
                selected_patient: selected_patient,
                selected_device: selected_device,
                start_date: start_date,
                end_date: end_date,
            },
            success: function (data) {
                $('.multi_recording_details').show();
                update_multi_night_summary_table(data.multi_night_summary)
                // //var multi_night_tst_data = JSON.parse(data.multi_night_tst_graphJSON);
                var multi_night_rem_nrem_sleep_graphJSON = JSON.parse(data.multi_night_rem_nrem_sleep_graphJSON);
                var multi_night_sleep_eff_data = JSON.parse(data.multi_night_sleep_eff_graphJSON);
                var multi_night_tib_tst_data = JSON.parse(data.multi_night_tib_tst_graphJSON);
                var multi_night_aweking_data = JSON.parse(data.multi_night_aweking_graphJSON);
                var sleep_trends_data = JSON.parse(data.sleep_trends_fig_graphJSON);
                var circadian_rhythms_data = JSON.parse(data.circadian_rhythms_graphJSON);
                var hear_rate_avg_fig_data = JSON.parse(data.hear_rate_avg_fig_graphJSON);

                Plotly.newPlot("multi_night_circadian_rhythms", circadian_rhythms_data.data, circadian_rhythms_data.layout);
                // //Plotly.newPlot("multi_night_tst", multi_night_tst_data.data, multi_night_tst_data.layout);
                Plotly.newPlot("multi_night_rem_nrem_sleep_tst", multi_night_rem_nrem_sleep_graphJSON.data, multi_night_rem_nrem_sleep_graphJSON.layout);
                Plotly.newPlot("multi_night_sleep_efficency", multi_night_sleep_eff_data.data, multi_night_sleep_eff_data.layout);
                Plotly.newPlot("multi_night_tib_tst", multi_night_tib_tst_data.data, multi_night_tib_tst_data.layout);
                Plotly.newPlot("multi_night_aweking", multi_night_aweking_data.data, multi_night_aweking_data.layout);
                Plotly.newPlot("sleep_trends", sleep_trends_data.data, sleep_trends_data.layout);
                Plotly.newPlot("hear_rate_avg", hear_rate_avg_fig_data.data, hear_rate_avg_fig_data.layout);

                $('.m_loading').hide();
                resize_graphs();
                $('.patient_multi_night_result').show();

            },
            error: function (error) {
                if (error?.responseJSON?.data?.login_required) {
                    location.href = "/";
                    localStorage.setItem("SESSION_EXP", true);
                }
                show_multi_night_err_message();
                $('.m_loading').hide()
                $('.patient_multi_night_result').hide();
            }
        });
    }

    function fetch_patient_details(username) {
        $('.loading').show();
        $('.m_loading').show();
        clear_err_message();
        clear_recording_details_times();
        $('.patient_result').hide();
        $('.multi_recording_details').hide();
        $('.patient_multi_night_result').hide();
        $.ajax({
            type: "GET",
            url: "/get_patient_details",
            data: {
                username: username
            },
            success: function (data) {
                update_patient_details(data);
                $('.loading').hide();
                $('.m_loading').hide();

            }
        })

    }

    function fetch_patient_question_ans(username) {

        $.ajax({
            type: "GET",
            url: "/get_patient_question_ans",
            data: {
                username: username
            },
            success: function (data) {
                update_patient_question_ans(data);

            }
        })

    }

    function update_patient_details(userDetails) {
        try {
            $('#patient_f_name').text(userDetails['fname'].charAt(0));
        } catch (error) {
            $('#patient_f_name').text('');
        }
        try {
            $('#patient_name').text(userDetails.name);
        } catch (error) {
            $('#patient_name').text('.....');
        }
        try {
            $('#patient_id').text(userDetails.PK.split('#')[1]);
        } catch (error) {
            $('#patient_id').text('.....');
        }
        try {
            $('#patient_g').text(userDetails.gender);
        } catch (error) {
            $('#patient_g').text('.....');
        }
        try {
            var dob = moment(userDetails.dob, "MMDDYYYY");
            $('#patient_dob').text(dob.format('MMM DD YYYY'));
        } catch (error) {
            $('#patient_dob').text('.....');
        }

    }

    function update_patient_question_ans(data) {

        var insomnia_qa = data.ins;
        var ins_sel = $('.insomnia_test ul');
        ins_sel.html('');
        var sleep_apnea_qa = data.sa;
        var sleep_apnea_sel = $('.sleep_apnea_test ul');
        sleep_apnea_sel.html('');
        var eds_qa = data.eds;
        var eds_sel = $('.eds_test ul');
        eds_sel.html('');
        var cr_qa = data.cr;
        var cr_sel = $('.rme_test ul');
        cr_sel.html('');
        if (insomnia_qa.length > 0) {
            $.each(insomnia_qa, function (index, val) {
                ins_sel.append('<li class="question">' + val["Q"] + '</li>');
                ins_sel.append('<li class="ans">' + val["A"] + '</li>');
            });
        } else {
            ins_sel.append('<li class="question"> Data not available </li>');
        }

        if (sleep_apnea_qa.length > 0) {
            $.each(sleep_apnea_qa, function (index, val) {
                sleep_apnea_sel.append('<li class="question">' + val["Q"] + '</li>');
                sleep_apnea_sel.append('<li class="ans">' + val["A"] + '</li>');
            });

        } else {
            sleep_apnea_sel.append('<li class="question"> Data not available </li>');
        }
        if (cr_qa.length > 0) {
            $.each(cr_qa, function (index, val) {
                cr_sel.append('<li class="question">' + val["Q"] + '</li>');
                cr_sel.append('<li class="ans">' + val["A"] + '</li>');
            });
        } else {
            cr_sel.append('<li class="question"> Data not available </li>');
        }
        if (eds_qa.length > 0) {
            $.each(eds_qa, function (index, val) {
                eds_sel.append('<li class="question">' + val["Q"] + '</li>');
                eds_sel.append('<li class="ans">' + val["A"] + '</li>');
            });
        } else {
            eds_sel.append('<li class="question"> Data not available </li>');
        }
    }


    function update_summary_table(data) {
        table_data = prepare_summary_table(data)
        var html_tbody = "";
        $.each(data, function (index, value) {
            var ref = value.ref ? value.ref : "";
            var label = value.label ? value.label : value.Metric;
            var res_value = value.formated_val ? value.formated_val : value.Value;
            html_tbody += '<tr>';
            html_tbody += `<td>${label} 
		<span data-toggle="tooltip" data-html="true" data-title="${value.def}" > <i class="fa fa-info-circle" aria-hidden="true"></i></span>`;


            if (value.res == 'neg') {
                html_tbody += '<td style="color: red">' + res_value + '</td>' + '<td>' + ref + '</td>';
            } else {
                html_tbody += '<td>' + res_value + '</td>' + '<td>' + ref + '</td>';
            }
            html_tbody += '<tr>';
        });
        $('#summary_table').html(html_tbody);
        $('[data-toggle="tooltip"]').tooltip()
        //update_result_analysis(table_data);


    }

    function update_multi_night_summary_table(data) {
        prepare_multi_night_summary_table(data);
        var html_tbody = "";
        $.each(data, function (index, value) {
            var label = value.label ? value.label : value.Metric;
            html_tbody += '<tr>';
            html_tbody += `<td>${label} 
		<span data-toggle="tooltip" data-html="true" data-title="${value.def}" > <i class="fa fa-info-circle" aria-hidden="true"></i></span>`;
            html_tbody += `<td>${value.formated_min}</td><td>${value.formated_max}</td><td>${value.formated_mean}</td>`

            html_tbody += '<tr>';
        });
        $('#multi_summary_table').html(html_tbody);
        $('[data-toggle="tooltip"]').tooltip()

    }

    function prepare_summary_table(data) {
        var patient_age_grup = get_patient_age_group(),
            recommended_sleep_value = get_sleep_recommended_val(patient_age_grup),
            recommended_sleep_value_in_sec = recommended_sleep_value * 60 * 60;
        var TST;
        var TST_in_sec;
        $.each(data, function (index, value) {
            if (value.Metric == "TST") {
                TST_in_sec = parseInt(value.Value);
                value['ref'] = "More than " + recommended_sleep_value + " Hours";
                value['res'] = TST_in_sec < recommended_sleep_value_in_sec ? "neg" : "pos";
                value['label'] = "Total Sleep Time - TST <span> (hr:min)</span>";
                value['formated_val'] = new Date(TST_in_sec * 1000).toISOString().substr(11, 5);
                value['def'] = `The Total Sleep Time (TST) is classified as sleep between In Bed 
			          (time patient got in to bed with the intent to fall asleep) and Out of Bed 
					  (time patient got out of bed with the intent to start their day)`;
            }
            if (value.Metric == "TIB") {
                TST_in_sec = parseInt(value.Value);
                value['label'] = "Time In Bed - TIB <span> (hr:min)</span>";
                value['formated_val'] = new Date(TST_in_sec * 1000).toISOString().substr(11, 5);
                value['def'] = `The total time in bed is defined as the number of minutes between In Bed and Out of Bed time`;
            } else if (value.Metric == "Sleep Latency") {
                var SL_in_min = parseInt(value.Value);
                value['ref'] = "Less than 20 min";
                value['res'] = SL_in_min > 20 ? "neg" : "pos";
                value['label'] = "Sleep Latency - SL <span> (hr:min)</span>";
                value['formated_val'] = new Date(SL_in_min * 60 * 1000).toISOString().substr(11, 5);
                value['def'] = `Sleep Latency is the total number of minutes after lights-off until the first epoch of sleep is recorded`;

            } else if (value.Metric == "Efficiency") {
                value['ref'] = "More than 85%";
                value['res'] = parseFloat(value.Value.split('%')[0]) < 85 ? "neg" : "pos";
                value['label'] = "Sleep Efficiency - SE <span>(%)</span>";
                value['def'] = `Sleep Efficiency is defined as the percentage of total sleep time over the time in bed`;
            } else if (value.Metric == "Wake Time") {
                var WT_in_sec = parseInt(value.Value),
                    value_to_compare = Math.round((TST_in_sec * 15) / 100);
                value['ref'] = "Less than 15% of TST";
                value['res'] = WT_in_sec > value_to_compare ? "neg" : "pos";
                value['label'] = "Wake time <span>(hr:min)</span>";
                value['formated_val'] = new Date(WT_in_sec * 1000).toISOString().substr(11, 5);
                value['def'] = `Wake time during Time in Bed (from when the patient go to bed to fall asleep until they get out of bed to start the day)`;
            } else if (value.Metric == "REM Latency") {
                var REML_in_sec = parseInt(value.Value);
                value['ref'] = "More than 8 min";
                if (REML_in_sec == 0) value['res'] = 'pos';
                else {
                    value['res'] = REML_in_sec < 8 * 60 ? "neg" : "pos";
                }
                value['label'] = "REM Latency - REML <span>(hr:min)</span>";
                value['formated_val'] = new Date(REML_in_sec * 1000).toISOString().substr(11, 5);
                value['def'] = `REM Latency is defined as the total number of minutes between the 
			               first epoch of sleep and the first epoch of REM sleep`;
            } else if (value.Metric == "REM Time") {
                var REM_in_sec = parseInt(value.Value),
                    value_to_compare = Math.round((TST_in_sec * 15) / 100);
                value['ref'] = "More than 15% of TST";
                value['res'] = REM_in_sec < value_to_compare ? "neg" : "pos";
                value['label'] = "REM Time <span>(hr:min)</span>";
                value['formated_val'] = new Date(REM_in_sec * 1000).toISOString().substr(11, 5);
                value['def'] = `REM sleep duration is defined as the total number of minutes of REM sleep between In Bed and Out of Bed time`;
            } else if (value.Metric == "WASO") {
                value['label'] = "Wake After Sleep Onset - WASO <span>(hr:min)</span>";
                value['formated_val'] = new Date(value.Value * 1000).toISOString().substr(11, 5);
                value['def'] = `Wake time after sleep onset is defined as the number of minutes a patient spends 
			                awake from the time the first epoch of sleep is recorded to the last epoch of sleep when the patient 
			                fully wakes up and does not attempt to return to sleep`;
            } else if (value.Metric == "NREM Time") {
                value['label'] = "NREM Time <span>(hr:min)</span>";
                value['formated_val'] = new Date(value.Value * 1000).toISOString().substr(11, 5);
                value['def'] = `NREM sleep duration is defined as the total number of minutes of NREM sleep between In Bed and Out of Bed time`;
            } else if (value.Metric == "Awakenings") {
                var tst_in_hr = Math.floor(TST_in_sec / 3600);
                value['ref'] = "Less than 6 per hour";
                value['res'] = value.Value > 6 * tst_in_hr ? "neg" : "pos";
                value['label'] = "Awakenings <span>(number)</span> ";
                value['def'] = `The number of awakenings is defined as the number of times a patient transitions 
			                from being asleep to being awake from the time the first epoch of sleep is recorded to 
							the time the patient fully wakes up and does not attempt to return to sleep`;
            }
        });
        return data;
    }

    function prepare_multi_night_summary_table(data) {

        $.each(data, function (index, value) {
            if (value.Metric == "TST") {
                value['label'] = "Total Sleep Time - TST <span> (hr:min)</span>";
                value['formated_max'] = new Date(value.max * 1000).toISOString().substr(11, 5);
                value['formated_min'] = new Date(value.min * 1000).toISOString().substr(11, 5);
                value['formated_mean'] = new Date(value.mean * 1000).toISOString().substr(11, 5);
                value['def'] = `The Total Sleep Time (TST) is classified as sleep between In Bed 
			          (time patient got in to bed with the intent to fall asleep) and Out of Bed 
					  (time patient got out of bed with the intent to start their day)`;
            }
            if (value.Metric == "TIB") {
                value['label'] = "Time In Bed - TIB <span> (hr:min)</span>";
                value['formated_max'] = new Date(value.max * 1000).toISOString().substr(11, 5);
                value['formated_min'] = new Date(value.min * 1000).toISOString().substr(11, 5);
                value['formated_mean'] = new Date(value.mean * 1000).toISOString().substr(11, 5);
                value['def'] = `The total time in bed is defined as the number of minutes between In Bed and Out of Bed time`;
            } else if (value.Metric == "Sleep Latency") {
                value['label'] = "Sleep Latency - SL <span> (hr:min)</span>";
                value['formated_max'] = new Date(value.max * 60 * 1000).toISOString().substr(11, 5);
                value['formated_min'] = new Date(value.min * 60 * 1000).toISOString().substr(11, 5);
                value['formated_mean'] = new Date(value.mean * 60 * 1000).toISOString().substr(11, 5);
                value['def'] = `Sleep Latency is the total number of minutes after lights-off until the first epoch of sleep is recorded`;

            } else if (value.Metric == "Efficiency") {
                value['label'] = "Sleep Efficiency - SE <span>(%)</span>";
                value['formated_max'] = value.max + '%';
                value['formated_min'] = value.min + '%';
                value['formated_mean'] = value.mean + '%';
                value['def'] = `Sleep Efficiency is defined as the percentage of total sleep time over the time in bed`;
            } else if (value.Metric == "Wake Time") {
                value['label'] = "Wake time <span>(hr:min)</span>";
                value['formated_max'] = new Date(value.max * 1000).toISOString().substr(11, 5);
                value['formated_min'] = new Date(value.min * 1000).toISOString().substr(11, 5);
                value['formated_mean'] = new Date(value.mean * 1000).toISOString().substr(11, 5);
                value['def'] = `Wake time during Time in Bed (from when the patient go to bed to fall asleep until they get out of bed to start the day)`;
            } else if (value.Metric == "REM Latency") {
                value['label'] = "REM Latency - REML <span>(hr:min)</span>";
                value['formated_max'] = new Date(value.max * 1000).toISOString().substr(11, 5);
                value['formated_min'] = new Date(value.min * 1000).toISOString().substr(11, 5);
                value['formated_mean'] = new Date(value.mean * 1000).toISOString().substr(11, 5);
                value['def'] = `REM Latency is defined as the total number of minutes between the 
			               first epoch of sleep and the first epoch of REM sleep`;
            } else if (value.Metric == "REM Time") {
                value['label'] = "REM Time <span>(hr:min)</span>";
                value['formated_max'] = new Date(value.max * 1000).toISOString().substr(11, 5);
                value['formated_min'] = new Date(value.min * 1000).toISOString().substr(11, 5);
                value['formated_mean'] = new Date(value.mean * 1000).toISOString().substr(11, 5);
                value['def'] = `REM sleep duration is defined as the total number of minutes of REM sleep between In Bed and Out of Bed time`;
            } else if (value.Metric == "WASO") {
                value['label'] = "Wake After Sleep Onset - WASO <span>(hr:min)</span>";
                value['formated_max'] = new Date(value.max * 1000).toISOString().substr(11, 5);
                value['formated_min'] = new Date(value.min * 1000).toISOString().substr(11, 5);
                value['formated_mean'] = new Date(value.mean * 1000).toISOString().substr(11, 5);
                value['def'] = `Wake time after sleep onset is defined as the number of minutes a patient spends 
			                awake from the time the first epoch of sleep is recorded to the last epoch of sleep when the patient 
			                fully wakes up and does not attempt to return to sleep`;
            } else if (value.Metric == "NREM Time") {
                value['label'] = "NREM Time <span>(hr:min)</span>";
                value['formated_max'] = new Date(value.max * 1000).toISOString().substr(11, 5);
                value['formated_min'] = new Date(value.min * 1000).toISOString().substr(11, 5);
                value['formated_mean'] = new Date(value.mean * 1000).toISOString().substr(11, 5);
                value['def'] = `NREM sleep duration is defined as the total number of minutes of NREM sleep between In Bed and Out of Bed time`;
            } else if (value.Metric == "Awakenings") {
                value['label'] = "Awakenings <span>(number)</span> ";
                value['formated_max'] = value.max;
                value['formated_min'] = value.min;
                value['formated_mean'] = value.mean;
                value['def'] = `The number of awakenings is defined as the number of times a patient transitions 
			                from being asleep to being awake from the time the first epoch of sleep is recorded to 
							the time the patient fully wakes up and does not attempt to return to sleep`;
            }
        });
        return data;
    }

    function get_patient_age_group() {
        var patient_dob = $('#patient_dob').text();
        var yeardiff = moment().diff(patient_dob, 'years', false);
        var monthsiff = moment().diff(patient_dob, 'months', false);
        var daysdiff = moment().diff(patient_dob, 'days', false);
        if (yeardiff > 0) {
            return yeardiff + '-years'
        }
        if (monthsiff > 0) {
            return monthsiff + '-months'
        }
        if (daysdiff > 0) {
            return daysdiff + '-days'
        }
    }

    function get_sleep_recommended_val(patient_age_grup) {
        var gruop_type = patient_age_grup.split("-")[1];
        var value = patient_age_grup.split("-")[0];
        var lookup_in = sleep_time_rec[gruop_type];
        for (var i = 0; i < lookup_in.length; i++) {
            var lookup_key = Object.keys(lookup_in[i])[0]
            var lookup_value = lookup_in[i][lookup_key]
            var range = lookup_key.split("-");
            if (parseInt(range[0]) <= parseInt(value) && parseInt(value) <= parseInt(range[1])) {
                return lookup_value;
            }
        }
    }

    function update_result_analysis(data) {
        function get_reslut_html(value) {
            var res_value = value.formated_val ? value.formated_val : value.Value;
            var html = '';
            if (value.res == 'pos') {
                html += '<h4 class="green">' + res_value + '</h4>';
                html += '<p><span class="arrow"><i class="fa fa-arrow-up" aria-hidden="true"></i></span>' + value.ref + '</p>';
            } else {
                html += '<h4 class="red">' + res_value + '</h4>';
                html += '<p><span class="arrow"><i class="fa fa-arrow-down" aria-hidden="true"></i></span>' + value.ref + '</p>';
            }
            return html;
        }

        $.each(data, function (index, value) {
            if (value.Metric == "TST") {
                $(".tst").html(get_reslut_html(value));
            } else if (value.Metric == "Efficiency") {
                $(".efficiency").html(get_reslut_html(value));
            } else if (value.Metric == "Sleep Latency") {
                $(".sleep_lat").html(get_reslut_html(value));
            } else if (value.Metric == "REM Latency") {
                $(".rem_lat").html(get_reslut_html(value));
            }
        });
    }

    $('#patient_select').on('change', function () {
        selected_patient = this.value;
        fetch_patient_details(selected_patient);
        fetch_patient_question_ans(selected_patient);
        clear_all();

    });

    $('#device_select').on('change', function (e) {
        selected_device = this.value;
        get_nights_dropdown(selected_patient, selected_device);
    });

    $('#m_device_select').on('change', function () {
        m_selected_device = this.value;
        get_multi_nights_dropdown(selected_patient, m_selected_device);
    });

    $('#n_device_select').on('change', function () {
        n_selected_device = this.value;
        get_multi_nights_dropdown(selected_patient, n_selected_device);
    });

    $('#night_select').on('change', function () {
        selected_night = this.value;
        fetch_patient_data(selected_patient, selected_device, selected_night)
    });

    picker.on('selected', (start_date, end_date) => {
        fetch_patient_multi_night_data(selected_patient, m_selected_device, start_date.dateInstance.toLocaleDateString(),
            end_date.dateInstance.toLocaleDateString())
        var date_range = $("#multi_night_select").val();
        update_multi_night_recording_times(date_range);
    });

    function show_err_message(error) {
        $('.err_' + error).fadeIn("slow");
    }

    function show_multi_night_err_message() {
        $('.m_err_patient_data').show();
    }

    function hide_multi_night_err_message() {
        $('.m_err_patient_data').hide();
    }

    function clear_err_message() {
        $('.err_block').hide();
    }

    function clear_all() {
        $('.recording_details').hide();
        $('.multi_recording_details').hide();
        $('.patient_result').hide();
        clear_err_message();
        clear_recording_details_times();
        $('#device_select').val(0);
        $('#device_select').niceSelect('update');
        update_night_dropdown([]);

    }

    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        var target = $(e.target).attr("href") // activated tab
        //TODO
    });

})