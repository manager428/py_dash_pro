$(document).ready(function() { 
 
	
	var device_select = document.getElementById('device_select');
	var age_select = document.getElementById('age_select');
	var cohort_select = document.getElementById('cohort_select');
	var gender_select = document.getElementById('gender_select');
	var user_select = document.getElementById('user_select');
	var selected_users, selected_device, selected_user,selected_age,selected_gender,selected_cohort;
	$('.group_data').hide()

    function get_group_data(){
		$.ajax({
			type:"GET",
			url: "/pre_val3_group_data",
			data: {
				selected_users: selected_users ? selected_users.toString(): null,
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
			url: "/pre_val3_individual_data",
			data: {
				selected_user: selected_user,
			},
			success: function(data){
			    $('.loading').hide();
				$('.group_data').show();	
				update_patient_details(data.user_details)
				update_individual_metrics_table(data.psg_minus_apple_metrics,data.psg_minus_fitbit_metrics,data.apple_minus_fitbit_metrics);
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

	function update_individual_metrics_table(psg_minus_apple_metrics,psg_minus_fitbit_metrics,apple_minus_fitbit_metrics ){

		var psg_minus_apple_html_tbody = '';
		var psg_minus_fitbit_html_tbody = '';
		var apple_minus_fitbit_html_tbody = '';
		$.each(psg_minus_apple_metrics, function(index, value){  
			var label_and_val = format_metrics_lable_and_value(value.Metric , value.Value)
			psg_minus_apple_html_tbody += '<tr>';
			psg_minus_apple_html_tbody += `<td>${label_and_val.lable} <span class='small'>Diff</span> </td><td>${label_and_val.value}</td>`
			psg_minus_apple_html_tbody += '<tr>';
		});
		$.each(psg_minus_fitbit_metrics, function(index, value){  
			var label_and_val = format_metrics_lable_and_value(value.Metric , value.Value)
			psg_minus_fitbit_html_tbody += `<tr><td>${label_and_val.value}</td><tr>`;
		});
		$.each(apple_minus_fitbit_metrics, function(index, value){  
			var label_and_val = format_metrics_lable_and_value(value.Metric , value.Value)
			apple_minus_fitbit_html_tbody += `<tr><td>${label_and_val.value}</td><tr>`;
		});
		$('#psg_minus_apple_table_body').html(psg_minus_apple_html_tbody);
		$('#psg_minus_fitbit_table_body').html(psg_minus_fitbit_html_tbody);
		$('#apple_minus_fitbit_table_body').html(apple_minus_fitbit_html_tbody);

	}

	

    $('#group_user_select').on('change', function() {
		selected_users = $('#group_user_select').val()
	});
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
		if(!selected_device || selected_device == 0){
			alert('Please select Device')
			return false;
		}
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