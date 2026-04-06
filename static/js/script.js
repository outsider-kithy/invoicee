//toggle
window.addEventListener('DOMContentLoaded',function(){
    var toggle=document.getElementById('toggle');
    var menu=document.getElementById('menu');
    
    toggle.onclick=function(){
        toggle.classList.toggle('open');
        menu.classList.toggle('open');
    }
});


    