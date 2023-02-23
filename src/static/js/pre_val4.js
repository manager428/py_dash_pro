$(document).ready(function() { 
 
	
	var device_select = document.getElementById('device_select');
	var age_select = document.getElementById('age_select');
	var cohort_select = document.getElementById('cohort_select');
	var gender_select = document.getElementById('gender_select');
	var user_select = document.getElementById('user_select');
	var selected_device, selected_user,selected_age,selected_gender,selected_cohort;
	$('.group_data').hide()

    function get_group_data(){
		$.ajax({
			type:"GET",
			url: "/pre_val3_group_data",
			data: {
				selected_device: selected_device,
				selected_cohort :selected_cohort,
				selected_age : selected_age,
				selected_gender : selected_gender,
			},
			success: function(data){
			   update_statics_table(data);
			},
			error: function (error) {
				if(error?.responseJSON?.data?.login_required){
					location.href = "/";
					localStorage.setItem("SESSION_EXP", true);
				}
				show_err_message('night_option');
				$('.loading').hide();
			}
		})

	}

	function get_individual_data(){
		$('.loading').show();
		$('.err_block').hide();
		$('.group_data').hide();

		$.ajax({
			type:"GET",
			url: "/pre_val4_individual_data",
			data: {
				selected_user: selected_user,
			},
			success: function(data){
			    $('.loading').hide();
				$('.group_data').show();	
				update_mslt_psg_statics(data.mslt_sleep_metrics_list)
				if(data.apple_sleep_metrics_list) update_apple_statics(data.apple_sleep_metrics_list)
				if(data.fitbit_sleep_metrics_list) update_fitbit_statics(data.fitbit_sleep_metrics_list)
				var mslt_psg_graphJSON = JSON.parse(data.mslt_psg_graphJSON);
				var apple_circadian_rhythms_graphJSON = JSON.parse(data.circadian_rhythms_apple_graphJSON);
				var fitbit_circadian_rhythms_graphJSON = JSON.parse(data.circadian_rhythms_fitbit_graphJSON);
				Plotly.newPlot("mslt_psg", mslt_psg_graphJSON.data, mslt_psg_graphJSON.layout);
				Plotly.newPlot("apple_circadian_rhythms", apple_circadian_rhythms_graphJSON.data, apple_circadian_rhythms_graphJSON.layout);
				Plotly.newPlot("fitbit_circadian_rhythms", fitbit_circadian_rhythms_graphJSON.data, fitbit_circadian_rhythms_graphJSON.layout);
				
			},
			error: function (error) {
				if(error?.responseJSON?.data?.login_required){
					location.href = "/";
					localStorage.setItem("SESSION_EXP", true);
				}
				$('.loading').hide();
				$('.err_individual').show();
			}
		})

	}

	function update_statics_table(table_data){
		var html_tbody = '';
		$.each(table_data, function(index, value){  
			var label_and_val_max = format_metrics_lable_and_value(value.Metric , value.max)
			var label_and_val_min = format_metrics_lable_and_value(value.Metric , value.min)
			var label_and_val_mean = format_metrics_lable_and_value(value.Metric , value.mean)
			html_tbody += '<tr>';
			html_tbody += `<td>${label_and_val_max.lable}</td><td>${label_and_val_max.value}</td><td>${label_and_val_min.value}</td>
			<td>${label_and_val_mean.value}</td>`
			html_tbody += '<tr>';
		});
		$('#statics_table_body').html(html_tbody);
	}

	function update_user_qa_ans(data){
		var ins_sel = $('.pre_val_1_insomnia_test ul');
		var sleep_apnea_sel = $('.pre_val_1_sleep_apnea_test ul');
		var eds_sel = $('.pre_val_1_eds_test ul');
		var cr_sel = $('.pre_val_1_rme_test ul');
		show_patient_question_ans(data, ins_sel,sleep_apnea_sel, eds_sel, cr_sel)
	}

	

	function get_metrics_value(metrics, array_of_metrics){
		return array_of_metrics.find(item => item.Metric == metrics).Value;
	}

	function update_mslt_psg_statics(mslt_sleep_metrics_list){
		var html_tbody = `<thead><tr><th>Nap </th><th>TST</th><th>TIB</th><th>Sleep Latency</th><th>REM Latency</th></tr></thead>`;
		html_tbody += `<tbody>`;
		$.each(mslt_sleep_metrics_list, function(index, value){  
			html_tbody += `<tr class="text-center"><td>${index}</td>`;
			html_tbody += `<td>${get_metrics_value('TST',value)}</td><td>${get_metrics_value('TIB',value)}</td>
			<td>${get_metrics_value('Sleep Latency',value)}</td><td>${get_metrics_value('REM Latency',value)}</td>`
			html_tbody += `</tr>`;
		});
		html_tbody += `</tbody>`;
		$('#mslt_psg_body').html(html_tbody);       
	}

	function update_apple_statics(apple_metrics_list){
		var html_tbody = `<thead><tr><th>Nap </th><th>TST</th><th>TIB</th><th>Sleep Latency</th><th>REM Latency</th></tr></thead>`;
		html_tbody += `<tbody>`;
		$.each(apple_metrics_list, function(index, value){  
			html_tbody += `<tr class="text-center"><td>${index}</td>`;
			html_tbody += `<td>${get_metrics_value('TST',value)}</td><td>${get_metrics_value('TIB',value)}</td>
			<td>${get_metrics_value('Sleep Latency',value)}</td><td>${get_metrics_value('REM Latency',value)}</td>`
			html_tbody += `</tr>`;
		});
		html_tbody += `</tbody>`;
		$('#apple_statics_body').html(html_tbody);
	}

	function update_fitbit_statics(fitbit_metrics_list){
		var html_tbody = `<thead><tr><th>Nap </th><th>TST</th><th>TIB</th><th>Sleep Latency</th><th>REM Latency</th></tr></thead>`;
		html_tbody += `<tbody>`;
		$.each(fitbit_metrics_list, function(index, value){  
			html_tbody += `<tr class="text-center"><td>${index}</td>`;
			html_tbody += `<td>${get_metrics_value('TST',value)}</td><td>${get_metrics_value('TIB',value)}</td>
			<td>${get_metrics_value('Sleep Latency',value)}</td><td>${get_metrics_value('REM Latency',value)}</td>`
			html_tbody += `</tr>`;
		});
		html_tbody += `</tbody>`;
		$('#fitbit_statics_body').html(html_tbody);
	}


	$('#device_select').on('change', function() {
		selected_device= this.value;
	});

	$('#cohort_select').on('change', function() {
		selected_cohort = this.value;
	});
	$('#age_select').on('change', function() {
		selected_age = this.value;
	});
	$('#gender_select').on('change', function() {
		selected_gender = this.value;
	});
	
	$('#filter_grp_data').on('click', function() {
		get_group_data()
	});
	$('#user_select').on('change', function() {
		selected_user= this.value;
		get_individual_data()
	});

	$('#print_page').click(function(){
		window.print();
    });



})