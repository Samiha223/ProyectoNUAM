from django.urls import path
from tributacion import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),
    path('api/buscar/', views.buscar_calificaciones, name='buscar_calificaciones'),
    path('api/guardar/', views.guardar_calificacion, name='guardar_calificacion'),
    path('api/eliminar/', views.eliminar_calificacion, name='eliminar_calificacion'),
    path('api/csv/previsualizar/', views.previsualizar_csv, name='previsualizar_csv'),
    path('api/csv/confirmar/', views.confirmar_carga_masiva, name='confirmar_carga_masiva'),
    path('api/logs/', views.ver_logs, name='ver_logs'),
]
