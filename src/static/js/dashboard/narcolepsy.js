let n_selected_device;
let n_selected_options = ['Sleep-Dialy', 'Karolinska-Scale']
const n_picker = new Litepicker({
    element: document.getElementById('narcolepsy_night_select'),
    singleMode: false,
    allowRepick: true
});
let nacolepsy_graphJSON

$(document).ready(function () {
    $('.narcolepsy_details').hide();
    $('.patient_narcolepsy_result').hide();

    $('#n_device_select').on('change', function () {
        n_selected_device = this.value;
        get_narcolelsy_multi_nights_dropdown(selected_patient, n_selected_device);
    });

    n_picker.on('selected', (start_date, end_date) => {
        fetch_patient_narcolepsy_data(selected_patient, n_selected_device, start_date.dateInstance.toLocaleDateString(),
            end_date.dateInstance.toLocaleDateString())
        var date_range = $("#narcolepsy_night_select").val();
        update_narcolepsy_recording_times(date_range);
    });

    $('input[name="sleepiness-option"]').click(function(){
        n_selected_options = [];
        $('input[name="sleepiness-option"]:checked').each(function(){
            n_selected_options.push($(this).val())
            updateChart()
        });
        if (n_selected_options.length === 0) {
            updateChart()
        }
    });
})

function clear_narcolepsy_recording_times() {
    $('#narcolepsy_recording_start_date').text("");
    $('#narcolepsy_recording_end_date').text("");
    $('#narcolepsy_recording_device').text("");
}

function get_narcolelsy_multi_nights_dropdown(selected_patient, selected_device) {
    $('.m_loading').show();
    $('.narcolepsy_details').hide();
    $('.patient_narcolepsy_result').hide();
    $.ajax({
        type: "GET",
        url: "/patient_night_options",
        data: {
            selected_patient: selected_patient,
            selected_device: selected_device,
        },
        success: function (data) {
            highlight_narcolepsy_option(data);
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

function hide_narcolepsy_err_message(){
	$('.n_err_patient_data').hide();
}

function highlight_narcolepsy_option(data) {
    var night_options = data;
    var highlighted_days = night_options.map(x => new Date(x['label']));
    n_picker.setHighlightedDays(highlighted_days);
}

function fetch_patient_narcolepsy_data(selected_patient, selected_device, start_date, end_date) {
    $('.m_loading').show();
    $('.patient_narcolepsy_result').hide();
    $('.narcolepsy_details').hide();
    hide_narcolepsy_err_message();
    clear_narcolepsy_recording_times()

    $.ajax({
        type: "GET",
        url: "/get_patient_narcolepsy_data",
        data: {
            selected_patient: selected_patient,
            selected_device: selected_device,
            start_date: start_date,
            end_date: end_date,
        },
        success: function (data) {
            $('.narcolepsy_details').show();
            nacolepsy_graphJSON = JSON.parse(data.nacolepsy_graphJSON);
            updateChart()
            $('.m_loading').hide();
            resize_graphs();
            $('.patient_narcolepsy_result').show();
            var nacolepsy_naps_graphJSON = JSON.parse(data.nacolepsy_naps_graphJSON);
            var nacolepsy_sleep_graphJSON = JSON.parse(data.nacolepsy_sleep_graphJSON);
            var nacolepsy_rem_graphJSON = JSON.parse(data.nacolepsy_rem_graphJSON);
            Plotly.newPlot("narcolepsy_naps", nacolepsy_naps_graphJSON.data, nacolepsy_naps_graphJSON.layout);
            Plotly.newPlot("narcolepsy_sleep", nacolepsy_sleep_graphJSON.data, nacolepsy_sleep_graphJSON.layout);
            Plotly.newPlot("narcolepsy_rtm", nacolepsy_rem_graphJSON.data, nacolepsy_rem_graphJSON.layout);

        },
        error: function (error) {
            if (error.responseJSON.data.login_required) {
                location.href = "/";
                localStorage.setItem("SESSION_EXP", true);
            }
            show_err_message();
            $('.m_loading').hide()
            $('.patient_narcolepsy_result').hide();
        }
    });
}

function updateChart() {
    console.log(nacolepsy_graphJSON)
    let filteredData = nacolepsy_graphJSON.data.filter(n => n_selected_options.indexOf(n.name) > -1);
    console.log(filteredData)
    Plotly.newPlot("narcolepsy_circadian_rhythms", filteredData, nacolepsy_graphJSON.layout);
}

function update_narcolepsy_recording_times(date_range) {
    var date_range_arr = date_range.split(" - ");
    $('#narcolepsy_recording_start_date').text(date_range_arr[0]);
    $('#narcolepsy_recording_end_date').text(date_range_arr[1]);
    $('#narcolepsy_recording_device').text(get_recording_device_name(n_selected_device));
    $('#narcolepsy_recording_device_image').attr("src", '/static/images/' + n_selected_device + '.png');
}


function prepare_narcolepsy_summary_table(data) {

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
