$(document).ready(function() { 
 
	
	var device_select = document.getElementById('device_select');
	var age_select = document.getElementById('age_select');
	var cohort_select = document.getElementById('cohort_select');
	var gender_select = document.getElementById('gender_select');
	var user_select = document.getElementById('user_select');
	var selected_users, selected_device, selected_user,selected_age,selected_gender,selected_cohort;
	$('.group_data').hide()

    function get_group_data(){
		$('.loading').show();
		$('.err_block').hide();
		$.ajax({
			type:"GET",
			url: "/pre_val1_group_data",
			data: {
				selected_users: selected_users ? selected_users.toString(): null,
				selected_device: selected_device,
				selected_cohort :selected_cohort,
				selected_age : selected_age,
				selected_gender : selected_gender,
			},
			success: function(data){
			   update_statics_table(data.statics_dict);
			   if (data.eval_statics_intersection){
				 $('#eval_table_intersection').html(data.eval_statics_intersection)
			   } 
			   if (data.eval_statics_union){
				$('#eval_table_union').html(data.eval_statics_union)
			  }   
			   $('#users_in_group_analysis').html(`( ${data.total_users} Results )`)
			   $('.loading').hide();
			},
			error: function (error) {
				if(error?.responseJSON?.data?.login_required){
					location.href = "/";
					localStorage.setItem("SESSION_EXP", true);
				}
				$('.err_group').show();
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
			url: "/pre_val1_individual_data",
			data: {
				selected_user: selected_user,
			},
			success: function(data){
			    $('.loading').hide();
				$('.group_data').show();	
				update_patient_details(data.user_details)
				if (data.eval_statics_apple_intersection){
					$('#ind_eval_apple_table_intersection').html(data.eval_statics_apple_intersection)
				} 
				if (data.eval_statics_apple_union){
					$('#ind_eval_apple_table_union').html(data.eval_statics_apple_union)
				} 
				if (data.eval_statics_fitbit_intersection){
					$('#ind_eval_fitbit_table_intersection').html(data.eval_statics_fitbit_intersection)
				} 
				if (data.eval_statics_fitbit_union){
					$('#ind_eval_fitbit_table_union').html(data.eval_statics_fitbit_union)
				}   
				update_individual_metrics_table(data.apple_sleep_metrics_data,data.fitbit_sleep_metrics_data,data.psg_sleep_metrics_data)
				var apple_circadian_rhythms_graphJSON = JSON.parse(data.circadian_rhythms_apple_graphJSON);
				var fitbit_circadian_rhythms_graphJSON = JSON.parse(data.circadian_rhythms_fitbit_graphJSON);
				var psg_circadian_rhythms_graphJSON = JSON.parse(data.circadian_rhythms_psg_graphJSON);
				Plotly.newPlot("apple_circadian_rhythms", apple_circadian_rhythms_graphJSON.data, apple_circadian_rhythms_graphJSON.layout);
				Plotly.newPlot("fitbit_circadian_rhythms", fitbit_circadian_rhythms_graphJSON.data, fitbit_circadian_rhythms_graphJSON.layout);
				Plotly.newPlot("psg_circadian_rhythms", psg_circadian_rhythms_graphJSON.data, psg_circadian_rhythms_graphJSON.layout);
				update_quality_issues(data.quality_issues)
				update_user_qa_ans(data.user_que_ans)

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
		var html_header = `<tr><th>Metrics</th><th >Max</th><th >Min</th><th >Avg</th><th >Std</th></tr>`;
		$('#statics_table > thead').html(html_header);
		var html_tbody = '';
		$.each(table_data, function(index, value){  
			var label_and_val_max = format_metrics_lable_and_value(value.Metric , value.max)
			var label_and_val_min = format_metrics_lable_and_value(value.Metric , value.min)
			var label_and_val_mean = format_metrics_lable_and_value(value.Metric , value.mean)
			var label_and_val_std = format_metrics_lable_and_value(value.Metric , value.std)
			html_tbody += '<tr>';
			html_tbody += `<td>${label_and_val_max.lable}</td><td>${label_and_val_max.value}</td><td>${label_and_val_min.value}</td>
			<td>${label_and_val_mean.value}</td><td>${label_and_val_std.value}</td>`
			html_tbody += '</tr>';
		});
		$('#statics_table > tbody').html(html_tbody);
	}

	function update_user_qa_ans(data){
		var ins_sel = $('.pre_val_1_insomnia_test ul');
		var sleep_apnea_sel = $('.pre_val_1_sleep_apnea_test ul');
		var eds_sel = $('.pre_val_1_eds_test ul');
		var cr_sel = $('.pre_val_1_rme_test ul');
		show_patient_question_ans(data, ins_sel,sleep_apnea_sel, eds_sel, cr_sel)
	}

	function update_individual_metrics_table(apple_metrics, fitbit_metrics, psg_metrics ){
		var patient_age_grup  = get_patient_age_group($('#patient_dob'));
		var recommended_sleep_value = get_sleep_recommended_val(patient_age_grup);
		var apple_summary_table_data = prepare_summary_table(apple_metrics, recommended_sleep_value);
		var fitbit_summary_table_data = prepare_summary_table(fitbit_metrics, recommended_sleep_value);
		var psg_summary_table_data = prepare_summary_table(psg_metrics, recommended_sleep_value);
		update_summary_table(apple_summary_table_data, $('#apple_table_body') , false,true,false)
		update_summary_table(fitbit_summary_table_data,$('#fitbit_table_body'),false,true,false)
		update_summary_table(psg_summary_table_data,$('#psg_table_body'),false,true,false)
	}

	function update_quality_issues(data){
		$('#apple_issue').html(`<p> Quality Issue : ${data.apple}</p>`);
		$('#fitbit_issue').html(`<p> Quality Issue : ${data.fitbit}</p>`);
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