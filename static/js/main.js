$(document).ready(function() {
    $('#checkNumQr').on('click', function(){
        var numQr = $('#input_qr').val()
        console.log(numQr)
        $.ajax({
            type: "POST",
            url: "/show_qrcode",
            data: JSON.stringify({numQr: numQr}),
            contentType: 'application/json',
            success: function (response) {
                if(response.result !== false) {
                    $('#qrcode').attr('src', response.path)
                    $('#qrcode').css('opacity', 1)
                }
                else {
                    alert('Error generating QR code');
                }
            }
        });
    })

    $('#input_qr').keydown(function(){
        $('#qrcode').css('opacity', 0)
        $('#qrcode').attr('src', '/static/images/coaster.png')
    })
    let num_photos_printed = -1;
    function fetchPhotosPrinted() {
        $.ajax({
            type: "GET",
            url: "/get_photos_printed",
            success: function (response) {
                file_count = response.file_count
                $('#today').html('Ngày: ' + response.today)
                if(file_count != num_photos_printed) {
                    $('#photos_printed').html(file_count + ' Hình Ảnh')
                    var cost = file_count * 150000
                    $('#total_cost').html(new Intl.NumberFormat('de-DE').format(cost) + ' VNĐ')
                }
                else {
                    alert('error')
                }
            }
        });
    }

    function fetchPhotosPrintedHt() {
        $.ajax({
            type: "GET",
            url: "/get_photos_printed_ht",
            success: function (response) {
                console.log(response.file_customer);
                
                if(response.file_count != num_photos_printed) {
                    $('#photos_printed_ht').html(response.file_count + ' Hình Ảnh')
                    $('#photo_standard').html(response.file_stand)
                    $('#photo_full').html(response.file_full)
                    $('#photo_extra').html(response.file_extra)
                    $('#photo_customer').html(response.file_customer)
                }
                else {
                    alert('error')
                }
            }
        });
    }
    fetchPhotosPrinted()
    fetchPhotosPrintedHt()
    setInterval(fetchPhotosPrinted, 60000)
    setInterval(fetchPhotosPrintedHt, 120000)
});
