var selected_device;
var selected_night;
var night_select = document.getElementById('night_select');
var device_select = document.getElementById('device_select');
$(document).ready(function () {
    $('.patient_result').hide();
    $('.recording_details').hide();
    $('#device_select').on('change', function (e) {
        selected_device = this.value;
        get_nights_dropdown(selected_patient, selected_device);
    });

    $('#night_select').on('change', function () {
        selected_night = this.value;
        fetch_summary(selected_patient, selected_device, selected_night)
		update_recording_details_times();
		$('.recording_details').show();
        // fetch_patient_data(selected_patient, selected_device, selected_night)
    });
})


function show_multi_night_err_message(){
	$('.m_err_patient_data').show();
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
            if (error.responseJSON.data.login_required) {
                location.href = "/";
                localStorage.setItem("SESSION_EXP", true);
            }
            show_err_message('night_option');
            $('.loading').hide();
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

function fetch_summary(selected_patient, selected_device, selected_night) {
    clear_err_message();
    clear_recording_details_times();
    $('.loading').show();
    $.ajax({
        type: "GET",
        url: "/get-one-night-summary",
        data: {
            selected_patient: selected_patient,
            selected_device: selected_device,
            selected_night: selected_night,
        },
        success: function (resp) {
            update_summary_table(resp.summary);
			$('.patient_result').show();
			$('.loading').hide();
			var hr_fig_data = JSON.parse(resp.hr_fig_graphJSON);
			var hrv_fig_data = JSON.parse(resp.hrv_fig_graphJSON);
			var activity_fig_data = JSON.parse(resp.activity_fig_graphJSON);
			var hypnogram_data = JSON.parse(resp.hypnogram_graphJSON);
			var hypnodensity_data = JSON.parse(resp.hypnodensity_graphJSON);
			
			Plotly.newPlot("hr_graph", hr_fig_data.data, hr_fig_data.layout);
			Plotly.newPlot("hrv_graph", hrv_fig_data.data, hrv_fig_data.layout);
			Plotly.newPlot("activity_graph", activity_fig_data.data, activity_fig_data.layout);
			Plotly.newPlot("hypnogram", hypnogram_data.data, hypnogram_data.layout);
			Plotly.newPlot("hypnodensity", hypnodensity_data.data, hypnodensity_data.layout);
			resize_graphs();
			
        },
        error: function (error) {
            if (error.responseJSON.data.login_required) {
                location.href = "/";
                localStorage.setItem("SESSION_EXP", true);
            }
            show_err_message('patient_data');
			$('.patient_result').show();
			$('.loading').hide();
        }
    });
}

function update_summary_table(data){
    const table_data = prepare_summary_table(data)
	var html_tbody = "";
	$.each(table_data, function(index, value){
		var ref = value.ref ? value.ref : "";
		var label = value.label ? value.label : value.Metric;
		var res_value = value.formated_val ? value.formated_val : value.Value;
		html_tbody += '<tr>';
		html_tbody += `<td>${label} 
		<span data-toggle="tooltip" data-html="true" data-title="${value.def}" > <i class="fa fa-info-circle" aria-hidden="true"></i></span>`;


		if(value.res == 'neg'){
			html_tbody += '<td style="color: red">'+res_value+'</td>'+'<td>'+ref+'</td>';
		}
		else{
			html_tbody += '<td>'+res_value+'</td>'+'<td>'+ref+'</td>';
		}
	    html_tbody += '<tr>';
	});
	$('#summary_table').html(html_tbody);
	$('[data-toggle="tooltip"]').tooltip()
}

function prepare_summary_table(summary_data){
	var patient_age_grup = get_patient_age_group();
	let recommended_sleep_value = get_sleep_recommended_val(patient_age_grup),
	recommended_sleep_value_in_sec = recommended_sleep_value*60*60;
	var TST ;
	var TST_in_sec ;
	const values = []
	$.each(summary_data, function(label, data){
		let value = {label, Value: data}
		if (label === 'PK' || label === 'SK') {

		}
		if(label === "TST"){
			TST_in_sec = data;
			value['ref'] = "More than "+recommended_sleep_value+" Hours";
			value['res'] = TST_in_sec < recommended_sleep_value_in_sec ? "neg" : "pos";
			value['label'] = "Total Sleep Time - TST <span> (hr:min)</span>";
			value['formated_val'] = new Date(TST_in_sec * 1000).toISOString().substr(11, 5) ;
			value['def'] = `The Total Sleep Time (TST) is classified as sleep between In Bed 
			          (time patient got in to bed with the intent to fall asleep) and Out of Bed 
					  (time patient got out of bed with the intent to start their day)` ;
		}
		if(label === "TIB"){
			TST_in_sec = data;
			value['label'] = "Time In Bed - TIB <span> (hr:min)</span>";
			value['formated_val'] = new Date(TST_in_sec * 1000).toISOString().substr(11, 5) ;
			value['def'] = `The total time in bed is defined as the number of minutes between In Bed and Out of Bed time` ;
		}
		else if(label === "SleepLatency" ){
			var SL_in_min = data;
			value['ref'] = "Less than 20 min";
			value['res'] = SL_in_min > 20 ? "neg" : "pos";
			value['label'] = "Sleep Latency - SL <span> (hr:min)</span>";
			value['formated_val'] = new Date(SL_in_min * 60 * 1000).toISOString().substr(11, 5) ;
			value['def'] = `Sleep Latency is the total number of minutes after lights-off until the first epoch of sleep is recorded`;

		}
		else if(label === "Efficiency" ){
			value['ref'] = "More than 85%";
			value['res'] = parseFloat(data.split('%')[0])  < 85 ? "neg" : "pos";
			value['label'] ="Sleep Efficiency - SE <span>(%)</span>";
			value['def'] = `Sleep Efficiency is defined as the percentage of total sleep time over the time in bed`;
		}
		else if(label === "WAKE" ){
			let WT_in_sec = data,
			value_to_compare =  Math.round((TST_in_sec * 15) / 100);
			value['ref'] = "Less than 15% of TST";
			value['res'] = WT_in_sec > value_to_compare ? "neg" : "pos";
			value['label'] ="Wake time <span>(hr:min)</span>";
			value['formated_val'] = new Date(WT_in_sec * 1000).toISOString().substr(11, 5) ;
			value['def'] = `Wake time during Time in Bed (from when the patient go to bed to fall asleep until they get out of bed to start the day)` ;
		}
		else if(label === "REMLatency" ){
			const REML_in_sec = data;
			value['ref'] = "More than 8 min";
			if (REML_in_sec === 0) value['res'] ='pos';
			else{
				value['res'] = REML_in_sec < 8*60 ? "neg" : "pos";
			}
			value['label'] ="REM Latency - REML <span>(hr:min)</span>";
			value['formated_val'] = new Date(REML_in_sec * 1000).toISOString().substr(11, 5) ;
			value['def'] = `REM Latency is defined as the total number of minutes between the 
			               first epoch of sleep and the first epoch of REM sleep`;
		}
		else if(label === "REMTime" ){
			var REM_in_sec = data,
			value_to_compare =  Math.round((TST_in_sec * 15) / 100);
			value['ref'] = "More than 15% of TST";
			value['res'] = REM_in_sec < value_to_compare ? "neg" : "pos";
			value['label'] ="REM Time <span>(hr:min)</span>";
			value['formated_val'] = new Date(REM_in_sec * 1000).toISOString().substr(11, 5) ;
			value['def'] = `REM sleep duration is defined as the total number of minutes of REM sleep between In Bed and Out of Bed time` ;
		}
		else if(label === "WASO" ){
			value['label'] ="Wake After Sleep Onset - WASO <span>(hr:min)</span>";
			value['formated_val'] = new Date(data * 1000).toISOString().substr(11, 5) ;
			value['def'] = `Wake time after sleep onset is defined as the number of minutes a patient spends 
			                awake from the time the first epoch of sleep is recorded to the last epoch of sleep when the patient 
			                fully wakes up and does not attempt to return to sleep`;
		}
		else if(label === "NREMTime" ){
			value['label'] ="NREM Time <span>(hr:min)</span>";
			value['formated_val'] = new Date(data * 1000).toISOString().substr(11, 5) ;
			value['def'] = `NREM sleep duration is defined as the total number of minutes of NREM sleep between In Bed and Out of Bed time` ;
		}
		else if(label === "Awakenings" ){
			var tst_in_hr = Math.floor(TST_in_sec / 3600);
			value['ref'] = "Less than 6 per hour";
			value['res'] = data > 6*tst_in_hr ? "neg" : "pos";
			value['label'] ="Awakenings <span>(number)</span> ";
			value['def'] = `The number of awakenings is defined as the number of times a patient transitions 
			                from being asleep to being awake from the time the first epoch of sleep is recorded to 
							the time the patient fully wakes up and does not attempt to return to sleep`;
		}
		else if(label === "BedTime" ){
			value['label'] ="Bed Time ";
			value['formated_val'] = data;
			value['def'] = `Bed Time`;
		}
		else if(label === "OutOfBedTime" ){
			value['label'] ="Out of Bed Time ";
			value['formated_val'] = data ;
			value['def'] = `Out of Bed Time`;
		}
		values.push(value);
	});
	return values;
}

function resize_graphs() {
	var d3 = Plotly.d3;
	gd3 = d3.selectAll('.graph_area')[0];
	$.each(gd3, function (index, elm) {
		Plotly.Plots.resize(elm);
	});
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
            if (error.responseJSON.data.login_required) {
                location.href = "/";
                localStorage.setItem("SESSION_EXP", true);
            }
            show_err_message('patient_data');
            $('.loading').hide();
            $('.patient_result').hide();
        }
    });
}


function update_recording_details_times() {
	let end_date = selected_night.split('/')[0];
	let year = parseInt(end_date.substring(0, 4));
	let month = parseInt(end_date.substring(4, 6));
	let day = parseInt(end_date.substring(6, 8));
	end_date = new Date(year, month-1, day, 12, 0, 0);
	let start_date = new Date(end_date.getTime() - 24 * 60 * 60000)
    $('#recording_start_date').text(start_date.toLocaleString());
    $('#recording_end_date').text(end_date.toLocaleString());
    $('#recording_quality').text('1200.0s missing data,');
    $('#recording_device').text(get_recording_device_name(selected_device));
    $('#recording_device_image').attr("src", '/static/images/' + selected_device + '.png');
	$('#recording_date').text(end_date.getDate());
    $('#recording_month').text(end_date.toLocaleString('default', {month: 'short'}));
    $('#recording_year').text(end_date.getFullYear());
}


function get_patient_age_group(){
	var patient_dob = $('#patient_dob').text();
	var yeardiff = moment().diff(patient_dob, 'years',false);
	var monthsiff = moment().diff(patient_dob, 'months',false);
	var daysdiff = moment().diff(patient_dob, 'days',false);
    if (yeardiff > 0){
		return yeardiff+'-years'
	}
	if (monthsiff > 0){
		return monthsiff+'-months'
	}
	if (daysdiff > 0){
		return daysdiff+'-days'
	}
}

function get_sleep_recommended_val(patient_age_grup){
   var gruop_type = patient_age_grup.split("-")[1];
   var value  = patient_age_grup.split("-")[0];
   var lookup_in = sleep_time_rec[gruop_type];
   for (var i=0; i<lookup_in.length;i++ ){
	   var lookup_key = Object.keys(lookup_in[i])[0]
	   var lookup_value = lookup_in[i][lookup_key]
	    var range = lookup_key.split("-");
        if (parseInt(range[0]) <= parseInt(value) && parseInt(value) <= parseInt(range[1])){
          return lookup_value;
		}
   }
}

