function formData(cut_once) {
    var text = $('#labelText').val();
    if (text == '') text = ' ';
    return {
        text:        text,
        font_family: $('#fontFamily option:selected').text(),
        font_style:  $('#fontStyle option:selected').text(),
        font_size:   $('#fontSize').val(),
        label_size:  $('#labelSize option:selected').val(),
        align:       $('input[name=fontAlign]:checked').val(),
        orientation: $('input[name=orientation]:checked').val(),
        margin_top:    $('#marginTop').val(),
        margin_bottom: $('#marginBottom').val(),
        margin_left:   $('#marginLeft').val(),
        margin_right:  $('#marginRight').val(),
        print_type:    $('input[name=printType]:checked').val(),
        qrcode_size:   $('#qrCodeSize').val(),
        qrcode_correction: $('#qrCodeCorrection option:selected').val(),
        print_count:       $('#printCount').val(),
        print_color:       $('input[name=printColor]:checked').val(),
        line_spacing:      $('input[name=lineSpacing]:checked').val(),
        cut_once:          cut_once ? 1 : 0,
    }
}

function updatePreview(data) {
    $('#previewImg').attr('src', 'data:image/png;base64,' + data);
    var img = $('#previewImg')[0];
    img.onload = function() {
        $('#labelWidth').html( (img.naturalWidth /{{default_dpi}}*2.54).toFixed(1));
        $('#labelHeight').html((img.naturalHeight/{{default_dpi}}*2.54).toFixed(1));
    };
}

function updateStyles() {
    font_familiy = $('#fontFamily option:selected').text()

    $.ajax({
        type:        'POST',
        url:         '{{url_for('.get_font_styles')}}',
        contentType: 'application/x-www-form-urlencoded; charset=UTF-8',
        data:        {font: font_familiy},
        success: function( data ) {
            var styleSelect = $('#fontStyle');
            styleSelect.empty();
            $.each(data, function (key, value) {
                styleSelect.append($("<option></option>")
                    .attr("value", key).text(key));
                if ('Book,Regular'.includes(key)) {
                    styleSelect.val(key);
                }
            });
            styleSelect.trigger("change");
        }
    });
}

function preview() {
    if ($('#labelSize option:selected').data('round') == 'True') {
        $('img#previewImg').addClass('roundPreviewImage');
    } else {
        $('img#previewImg').removeClass('roundPreviewImage');
    }

    if ($('input[name=orientation]:checked').val() == 'standard') {
        $('.marginsTopBottom').prop('disabled', false).removeAttr('title');
        $('.marginsLeftRight').prop('disabled', true).prop('title', 'Only relevant if rotated orientation is selected.');
    } else {
        $('.marginsTopBottom').prop('disabled', true).prop('title', 'Only relevant if standard orientation is selected.');
        $('.marginsLeftRight').prop('disabled', false).removeAttr('title');
    }

    if ($('#labelSize option:selected').val().includes('red')) {
        $('#print_color_black').removeClass('disabled');
        $('#print_color_red').removeClass('disabled');
    } else {
        $('#print_color_black').addClass('disabled').prop('active', true);
        $('#print_color_red').addClass('disabled');
    }

    if($('input[name=printType]:checked').val() == 'image') {
        $('#groupLabelText').hide();
        $('#groupLabelImage').show()
    } else {
        $('#groupLabelText').show();
        $('#groupLabelImage').hide();
    }

    if($('input[name=printType]:checked').val() == 'image') {
        dropZoneMode = 'preview';
        imageDropZone.processQueue();
        return;
    }

    $.ajax({
        type:        'POST',
        url:         '{{url_for('.get_preview_from_image')}}?return_format=base64',
        contentType: 'application/x-www-form-urlencoded; charset=UTF-8',
        data:        formData(),
        success: function( data ) {
            updatePreview(data);
        }
    });
}

function setStatus(data) {
    if (data['success']) {
        $('#statusPanel').html('<div id="statusBox" class="alert alert-success" role="alert"><i class="fas fa-check"></i><span>Printing was successful.</span></div>');
    } else {
        $('#statusPanel').html('<div id="statusBox" class="alert alert-warning" role="alert"><i class="fas fa-exclamation-triangle"></i><span>Printing was unsuccessful:<br />'+data['message']+'</span></div>');
    }
    $('#printButton').prop('disabled', false);
    $('#dropdownPrintButton').prop('disabled', false);
}

function print(cut_once = false) {
    $('#printButton').prop('disabled', true);
    $('#dropdownPrintButton').prop('disabled', true);
    $('#statusPanel').html('<div id="statusBox" class="alert alert-info" role="alert"><i class="fas fa-hourglass-half"></i><span>Processing print request...</span></div>');

    if($('input[name=printType]:checked').val() == 'image') {
        dropZoneMode = 'print';
        imageDropZone.processQueue();
        return;
    }

    $.ajax({
        type:     'POST',
        dataType: 'json',
        data:     formData(cut_once),
        url:      '{{url_for('.print_text')}}',
        success:  setStatus,
        error:    setStatus
    });
}

updateStyles();
preview()


var imageDropZone;
Dropzone.options.myAwesomeDropzone = {
    url: function() {
        if (dropZoneMode == 'preview') {
            return "{{url_for('.get_preview_from_image')}}?return_format=base64";
        } else {
            return "{{url_for('.print_text')}}";
        }
    },
    paramName: "image",
    acceptedFiles: 'image/png,image/jpeg,application/pdf',
    maxFiles: 1,
    addRemoveLinks: true,
    autoProcessQueue: false,
    init: function() {
        imageDropZone = this;

        this.on("addedfile", function() {
            if (this.files[1] != null) {
                this.removeFile(this.files[0]);
            }
        });
    },

    sending: function(file, xhr, data) {
        // append all parameters to the request
        fd = formData(false);

        $.each(fd, function(key, value){
            data.append(key, value);
        });
    },

    success: function(file, response) {
        // If preview or print was successfull update the previewpane or print status
        if (dropZoneMode == 'preview') {
            updatePreview(response);
        } else {
            setStatus(response);
        }
        file.status = Dropzone.QUEUED;
    },

    accept: function(file, done) {
        // If a valid file was added, perform the preview
        done();
        preview();
    },

    removedfile: function(file) {
        file.previewElement.remove();
        preview();
        // Insert a dummy image
        updatePreview('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=');
    }
};
