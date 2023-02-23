var m_selected_device;
const picker = new Litepicker({
    element: document.getElementById('multi_night_select'),
    singleMode: false,
    allowRepick: true
});

$(document).ready(function () {
    $('.multi_recording_details').hide();
    $('.patient_multi_night_result').hide();

    $('#m_device_select').on('change', function () {
        m_selected_device = this.value;
        get_multi_nights_dropdown(selected_patient, m_selected_device);
    });

    picker.on('selected', (start_date, end_date) => {
        fetch_patient_multi_night_data(selected_patient, m_selected_device, start_date.dateInstance.toLocaleDateString(),
            end_date.dateInstance.toLocaleDateString())
        var date_range = $("#multi_night_select").val();
        update_multi_night_recording_times(date_range);
    });
})

function clear_multi_night_recording_times() {
    $('#multi_night_recording_start_date').text("");
    $('#multi_night_recording_end_date').text("");
    $('#multi_night_recording_device').text("");
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
            if (error.responseJSON.data.login_required) {
                location.href = "/";
                localStorage.setItem("SESSION_EXP", true);
            }
            show_err_message('night_option');
            $('.m_loading').hide();
        }
    })
}

function highlight_multi_night_option(data) {
    var night_options = data;
    var highlighted_days = night_options.map(x => new Date(x['label']));
    picker.setHighlightedDays(highlighted_days);
}

function hide_multi_night_err_message(){
	$('.m_err_patient_data').hide();
}

function fetch_patient_multi_night_data(selected_patient, selected_device, start_date, end_date) {
    $('.m_loading').show();
    $('.patient_multi_night_result').hide();
    $('.multi_recording_details').hide();
    hide_multi_night_err_message();
    clear_multi_night_recording_times()

    $.ajax({
        type: "GET",
        url: "/get-multiple-night-summary",
        data: {
            selected_patient: selected_patient,
            selected_device: selected_device,
            start_date: start_date,
            end_date: end_date,
        },
        success: function (data) {
            if (data.status) {
                update_multi_night_summary_table(data.multi_night_summary);
                var circadian_rhythms_data = JSON.parse(data.circadian_rhythms_graphJSON);
                Plotly.newPlot("multi_night_circadian_rhythms", circadian_rhythms_data.data, circadian_rhythms_data.layout);
                // //var multi_night_tst_data = JSON.parse(data.multi_night_tst_graphJSON);
                // var multi_night_rem_nrem_sleep_graphJSON = JSON.parse(data.multi_night_rem_nrem_sleep_graphJSON);
                // var multi_night_sleep_eff_data = JSON.parse(data.multi_night_sleep_eff_graphJSON);
                // var multi_night_tib_tst_data = JSON.parse(data.multi_night_tib_tst_graphJSON);
                // var multi_night_aweking_data = JSON.parse(data.multi_night_aweking_graphJSON);
                // var sleep_trends_data = JSON.parse(data.sleep_trends_fig_graphJSON);
                // var hear_rate_avg_fig_data = JSON.parse(data.hear_rate_avg_fig_graphJSON);

                
                // // //Plotly.newPlot("multi_night_tst", multi_night_tst_data.data, multi_night_tst_data.layout);
                // Plotly.newPlot("multi_night_rem_nrem_sleep_tst", multi_night_rem_nrem_sleep_graphJSON.data, multi_night_rem_nrem_sleep_graphJSON.layout);
                // Plotly.newPlot("multi_night_sleep_efficency", multi_night_sleep_eff_data.data, multi_night_sleep_eff_data.layout);
                // Plotly.newPlot("multi_night_tib_tst", multi_night_tib_tst_data.data, multi_night_tib_tst_data.layout);
                // Plotly.newPlot("multi_night_aweking", multi_night_aweking_data.data, multi_night_aweking_data.layout);
                // Plotly.newPlot("sleep_trends", sleep_trends_data.data, sleep_trends_data.layout);
                // Plotly.newPlot("hear_rate_avg", hear_rate_avg_fig_data.data, hear_rate_avg_fig_data.layout);
            }
            
            $('.multi_recording_details').show();
            $('.m_loading').hide();
            resize_graphs();
            $('.patient_multi_night_result').show();

        },
        error: function (error) {
            if (error.responseJSON.data.login_required) {
                location.href = "/";
                localStorage.setItem("SESSION_EXP", true);
            }
            show_multi_night_err_message();
            $('.m_loading').hide()
            $('.patient_multi_night_result').hide();
        }
    });
}


function update_multi_night_recording_times(date_range) {
    var date_range_arr = date_range.split(" - ");
    $('#multi_night_recording_start_date').text(date_range_arr[0]);
    $('#multi_night_recording_end_date').text(date_range_arr[1]);
    $('#multi_night_recording_device').text(get_recording_device_name(m_selected_device));
    $('#multi_recording_device_image').attr("src", '/static/images/' + m_selected_device + '.png');
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
