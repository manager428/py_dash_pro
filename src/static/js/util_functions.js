function show_patient_question_ans(data, ins_sel,sleep_apnea_sel, eds_sel, cr_sel){
	var insomnia_qa = data.ins;
	//var ins_sel = $('.insomnia_test ul');
	ins_sel.html('');
	var sleep_apnea_qa = data.sa;
	sleep_apnea_sel.html('');
	var eds_qa = data.eds;
	eds_sel.html('');
	var cr_qa = data.cr;
	cr_sel.html('');
	if(insomnia_qa.length > 0){
		$.each(insomnia_qa , function(index, val) { 
			ins_sel.append( '<li class="question">' + val["Q"] + '</li>' );
			ins_sel.append( '<li class="ans">' + val["A"] + '</li>' );
		});
	}
	else{
		ins_sel.append( '<li class="question"> Data not available </li>' );
	}

	if(sleep_apnea_qa.length > 0){
		$.each(sleep_apnea_qa , function(index, val) { 
			sleep_apnea_sel.append( '<li class="question">' + val["Q"] + '</li>' );
			sleep_apnea_sel.append( '<li class="ans">' + val["A"] + '</li>' );
		});

	}
	else{
		sleep_apnea_sel.append( '<li class="question"> Data not available </li>' );
	}
	if(cr_qa.length > 0){
        $.each(cr_qa , function(index, val) { 
			cr_sel.append( '<li class="question">' + val["Q"] + '</li>' );
			cr_sel.append( '<li class="ans">' + val["A"] + '</li>' );
		});	
	}
	else{
		cr_sel.append( '<li class="question"> Data not available </li>' );
	}if(eds_qa.length > 0){
		$.each(eds_qa , function(index, val) { 
			eds_sel.append( '<li class="question">' + val["Q"] + '</li>' );
			eds_sel.append( '<li class="ans">' + val["A"] + '</li>' );
		});
	}
	else{
		eds_sel.append( '<li class="question"> Data not available </li>' );
	}	
}

function update_patient_details(userDetails){
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
	}try {
		$('#patient_g').text(userDetails.gender);
	} catch (error) {
		$('#patient_g').text('.....');
	}try {
		var dob =moment(userDetails.dob , "MMDDYYYY");
	   $('#patient_dob').text(dob.format('MMM DD YYYY'));
	} catch (error) {
		$('#patient_dob').text('.....');
	}	
}

function format_metrics_lable_and_value(metrics,value){
	if(metrics == "TST"){
		var TST_in_sec = parseInt(value); 
		return {
			lable: "Total Sleep Time - TST <span> (hr:min)</span>",
			value : moment.duration(TST_in_sec, "seconds").format("h:mm", { trim: false})
		};
	}
	else if(metrics == "TIB"){
		var TIB_in_sec = parseInt(value);
		return {
			lable: "Time In Bed - TIB <span> (hr:min)</span>",
			value: moment.duration(TIB_in_sec, "seconds").format("h:mm", { trim: false})
		}; 
	}
	else if(metrics == "Sleep Latency" ){
		var SL_in_min = parseInt(value);
		return {
			lable: "Sleep Latency - SL <span> (hr:min)</span>",
			value: moment.duration(SL_in_min, "minutes").format("h:mm", { trim: false})
		};	
	}
	else if(metrics == "Efficiency" ){
		return {
			lable: "Sleep Efficiency - SE <span>(%)</span>",
			value: value.toFixed(2) + '%' ,
		};
	}
	else if(metrics == "Wake Time" ){
		var WT_in_sec = parseInt(value);
		return {
			lable: "Wake time <span>(hr:min)</span>",
			value: moment.duration(WT_in_sec, "seconds").format("h:mm", { trim: false})
		};
	}
	else if(metrics == "REM Latency" ){
		var REML_in_sec = parseInt(value);
		return {
			lable: "REM Latency - REML <span>(hr:min)</span>",
			value: moment.duration(REML_in_sec, "seconds").format("h:mm", { trim: false})
		};	
	}
	else if(metrics == "REM Time" ){
		var REM_in_sec = parseInt(value);
		return {
			lable: "REM Time <span>(hr:min)</span>",
			value: moment.duration(REM_in_sec, "seconds").format("h:mm", { trim: false})
		};
	}
	else if(metrics == "WASO" ){
		var waso_in_sec = parseInt(value);
		return {
			lable: "Wake After Sleep Onset - WASO <span>(hr:min)</span>",
			value: moment.duration(waso_in_sec, "seconds").format("h:mm", { trim: false})
		};
	}
	else if(metrics == "NREM Time" ){
		var NREM_in_sec = parseInt(value);
		return {
			lable: "NREM Time <span>(hr:min)</span>",
			value: moment.duration(NREM_in_sec, "seconds").format("h:mm", { trim: false})
		};
	}
	else if(metrics == "Awakenings" ){
		return {
			lable: "Awakenings <span>(number)</span>",
			value: value ,
		};
		
	}
}

function format_metrics_lable(value){
	
}

function prepare_summary_table( data , recommended_sleep_value){
	var recommended_sleep_value = recommended_sleep_value;
	var recommended_sleep_value_in_sec = recommended_sleep_value*60*60;
	var TST_in_sec ;
	$.each(data, function(index, value){
		if(value.Metric == "TST"){
			TST_in_sec = parseInt(value.Value); 
			value['ref'] = "More than "+recommended_sleep_value+" Hours";
			value['res'] = TST_in_sec < recommended_sleep_value_in_sec ? "neg" : "pos";
			value['label'] = "Total Sleep Time - TST <span> (hr:min)</span>";
			value['formated_val'] = new Date(TST_in_sec * 1000).toISOString().substr(11, 5) ;
			value['def'] = `The Total Sleep Time (TST) is classified as sleep between In Bed 
			          (time patient got in to bed with the intent to fall asleep) and Out of Bed 
					  (time patient got out of bed with the intent to start their day)` ;
		}
		else if(value.Metric == "TIB"){
			TST_in_sec = parseInt(value.Value); 
			value['label'] = "Time In Bed - TIB <span> (hr:min)</span>";
			value['formated_val'] = new Date(TST_in_sec * 1000).toISOString().substr(11, 5) ;
			value['def'] = `The total time in bed is defined as the number of minutes between In Bed and Out of Bed time` ;
		}
		else if(value.Metric == "Sleep Latency" ){
			var SL_in_min = parseInt(value.Value);
			value['ref'] = "Less than 20 min";
			value['res'] = SL_in_min > 20 ? "neg" : "pos";
			value['label'] = "Sleep Latency - SL <span> (hr:min)</span>";
			value['formated_val'] = new Date(SL_in_min * 60 * 1000).toISOString().substr(11, 5) ;
			value['def'] = `Sleep Latency is the total number of minutes after lights-off until the first epoch of sleep is recorded`;
			
		}
		else if(value.Metric == "Efficiency" ){
			value['ref'] = "More than 85%";
			var eff = !isNaN(Number(value.Value)) ? value.Value : parseFloat(value.Value.split('%')[0]);
			value['res'] = eff  < 85 ? "neg" : "pos";
			value['label'] ="Sleep Efficiency - SE <span>(%)</span>"; 
			value['def'] = `Sleep Efficiency is defined as the percentage of total sleep time over the time in bed`; 
		}
		else if(value.Metric == "Wake Time" ){
			var WT_in_sec = parseInt(value.Value),
			value_to_compare =  Math.round((TST_in_sec * 15) / 100);
			value['ref'] = "Less than 15% of TST";
			value['res'] = WT_in_sec > value_to_compare ? "neg" : "pos";
			value['label'] ="Wake time <span>(hr:min)</span>";
			value['formated_val'] = new Date(WT_in_sec * 1000).toISOString().substr(11, 5) ;
			value['def'] = `Wake time during Time in Bed (from when the patient go to bed to fall asleep until they get out of bed to start the day)` ;
		}
		else if(value.Metric == "REM Latency" ){
			var REML_in_sec = parseInt(value.Value);
			value['ref'] = "More than 8 min";
			if (REML_in_sec == 0) value['res'] ='pos';
			else{
				value['res'] = REML_in_sec < 8*60 ? "neg" : "pos";
			}	
			value['label'] ="REM Latency - REML <span>(hr:min)</span>";
			value['formated_val'] = new Date(REML_in_sec * 1000).toISOString().substr(11, 5) ;
			value['def'] = `REM Latency is defined as the total number of minutes between the 
			               first epoch of sleep and the first epoch of REM sleep`;
		}
		else if(value.Metric == "REM Time" ){
			var REM_in_sec = parseInt(value.Value),
			value_to_compare =  Math.round((TST_in_sec * 15) / 100);
			value['ref'] = "More than 15% of TST";
			value['res'] = REM_in_sec < value_to_compare ? "neg" : "pos";
			value['label'] ="REM Time <span>(hr:min)</span>";
			value['formated_val'] = new Date(REM_in_sec * 1000).toISOString().substr(11, 5) ;
			value['def'] = `REM sleep duration is defined as the total number of minutes of REM sleep between In Bed and Out of Bed time` ;
		}
		else if(value.Metric == "WASO" ){
			value['label'] ="Wake After Sleep Onset - WASO <span>(hr:min)</span>"; 
			value['formated_val'] = new Date(value.Value * 1000).toISOString().substr(11, 5) ;
			value['def'] = `Wake time after sleep onset is defined as the number of minutes a patient spends 
			                awake from the time the first epoch of sleep is recorded to the last epoch of sleep when the patient 
			                fully wakes up and does not attempt to return to sleep`;
		}
		else if(value.Metric == "NREM Time" ){
			value['label'] ="NREM Time <span>(hr:min)</span>"; 
			value['formated_val'] = new Date(value.Value * 1000).toISOString().substr(11, 5) ;
			value['def'] = `NREM sleep duration is defined as the total number of minutes of NREM sleep between In Bed and Out of Bed time` ;
		}
		else if(value.Metric == "Awakenings" ){
			var tst_in_hr = Math.floor(TST_in_sec / 3600);
			value['ref'] = "Less than 6 per hour";
			value['res'] = value.Value > 6*tst_in_hr ? "neg" : "pos";
			value['label'] ="Awakenings <span>(number)</span> ";
			value['def'] = `The number of awakenings is defined as the number of times a patient transitions 
			                from being asleep to being awake from the time the first epoch of sleep is recorded to 
							the time the patient fully wakes up and does not attempt to return to sleep`; 
		}
	});
	return data;
}
function update_summary_table(data,selector, show_ref,show_label,show_def){
    table_data = prepare_summary_table(data)
	var html_tbody = "";
	$.each(data, function(index, value){
		var ref = value.ref ? value.ref : "";
		var label = value.label ? value.label :value.Metric; 
		var res_value = value.formated_val ? value.formated_val : value.Value; 
		html_tbody += '<tr>';

        if(show_label){
			if(show_def){
				html_tbody += `<td>${label} 
				 <span data-toggle="tooltip" data-html="true" data-title="${value.def}" > <i class="fa fa-info-circle" aria-hidden="true"></i></span>`;
			}
			else{
				html_tbody += `<td>${label}`;
			}
		}
		if(show_ref){
			if(value.res == 'neg'){
				html_tbody += '<td style="color: red">'+res_value+'</td>'+'<td>'+ref+'</td>';
			}
			else{
				html_tbody += '<td>'+res_value+'</td>'+'<td>'+ref+'</td>';
			}
		}
		else{

			if(value.res == 'neg'){
				html_tbody += '<td style="color: red">'+res_value+'</td>';
			}
			else{
				html_tbody += '<td>'+res_value+'</td>';
			}

		}
	    html_tbody += '<tr>';
	});
	selector.html(html_tbody);
}
function get_patient_age_group(selector){
	var patient_dob = selector.text();
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