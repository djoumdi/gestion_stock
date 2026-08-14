from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from .models import Client
from accounts.notifications import enregistrer_action


@login_required
@permission_required('clients.view_client', raise_exception=True)
def liste_clients(request):
    clients = Client.objects.all().order_by('nom')
    for client in clients:
        client.nb_ventes = client.ventes.count()
        client.total_achats = sum(v.total for v in client.ventes.all())
    return render(request, 'clients/liste_clients.html', {'clients': clients})


@login_required
@permission_required('clients.add_client', raise_exception=True)
def ajouter_client(request):
    if request.method == 'POST':
        client = Client.objects.create(
            nom=request.POST.get('nom'),
            telephone=request.POST.get('telephone'),
            email=request.POST.get('email'),
        )
        return redirect('clients:detail_client', pk=client.pk)
    return render(request, 'clients/ajouter_client.html')


@login_required
@permission_required('clients.change_client', raise_exception=True)
def detail_client(request, pk):
    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        client.nom = request.POST.get('nom')
        client.telephone = request.POST.get('telephone')
        client.email = request.POST.get('email')
        client.save()
        return redirect('clients:detail_client', pk=client.pk)

    ventes = client.ventes.all().order_by('-date_vente')
    return render(request, 'clients/detail_client.html', {'client': client, 'ventes': ventes})


@login_required
@permission_required('clients.delete_client', raise_exception=True)
def supprimer_client(request, pk):
    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        nom = client.nom
        client.delete()
        enregistrer_action(request.user, f"a supprimé le client « {nom} »")
        messages.success(request, f"Client « {nom} » supprimé.")
        return redirect('clients:liste_clients')

    return redirect('clients:detail_client', pk=pk)
