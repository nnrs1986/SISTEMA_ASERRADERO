from django.urls import path
from . import views

urlpatterns = [
    path('', views.rolas_list, name='rolas_list'),
    path('crear/', views.rola_crear, name='rola_crear'),
    path('<int:pk>/', views.rola_detalle, name='rola_detalle'),
    path('<int:pk>/editar/', views.rola_editar, name='rola_editar'),
    path('<int:pk>/eliminar/', views.rola_eliminar, name='rola_eliminar'),
]
