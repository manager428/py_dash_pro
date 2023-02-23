var patient_options;
var selected_patient;
$(document).ready(function () {
    get_patients_dropdown();
    $('#patient_select').on('change', function () {
        selected_patient = this.value;
        fetch_patient_details(selected_patient);
        fetch_patient_question_ans(selected_patient);
        clear_all();
    });
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        var target = $(e.target).attr("href") // activated tab
        //TODO
    });
})


function show_err_message(error) {
    $('.err_' + error).fadeIn("slow");
}

function clear_err_message() {
    $('.err_block').hide();
}

function resize_graphs() {
    var d3 = Plotly.d3;
    gd3 = d3.selectAll('.graph_area')[0];
    $.each(gd3, function (index, elm) {
        Plotly.Plots.resize(elm);
    });
}

function clear_all() {
    $('.recording_details').hide();
    $('.multi_recording_details').hide();
    $('.narcolepsy_details').hide();
    $('.patient_result').hide();
    clear_err_message();
    clear_recording_details_times();
    $('#device_select').val(0);
    $('#device_select').niceSelect('update');
    $('#m_device_select').val(0);
    $('#m_device_select').niceSelect('update');
    update_night_dropdown([]);
}

function get_recording_device_name(selected_device) {
    if (selected_device === 'f') return "Fitbit Watch";
    if (selected_device === 'a') return "Apple Watch";
    if (selected_device === 'u') return "Apple Watch";
}

function clear_recording_details_times() {
    $('#recording_start_date').text("")
    $('#recording_end_date').text("")
    $('#recording_quality').text("")
    $('#recording_device').text("");
}

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
            if (error.responseJSON.data.login_required) {
                location.href = "/";
                localStorage.setItem("SESSION_EXP", true);
            }
            show_err_message('night_option');
            $('.loading').hide();
        }
    })
}

function update_patient_dropdown(dropdown_options, selected_option) {
    var patient_select = document.getElementById('patient_select');
    var patient_options = dropdown_options;
    for (var i = 0; i < patient_options.length; i++) {
        $(patient_select).append('<option id=' + patient_options[i].value + ' value=' + patient_options[i].value + '>' + patient_options[i].label.split('.').join(" ") + '</option>');
        if (patient_options[i].value == selected_option) {
            $('#patient_select').val(patient_options[i].value);
        }
    }
    $('#patient_select').niceSelect('update');
}

function fetch_patient_details(username) {
    $('.loading').show();
    $('.m_loading').show();
    clear_err_message();
    clear_recording_details_times();
    $('.patient_result').hide();
    $('.multi_recording_details').hide();
    $('.narcolepsy_details').hide();
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
