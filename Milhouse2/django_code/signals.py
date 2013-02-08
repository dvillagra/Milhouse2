
# Automatically create a UserProfile when a user is created
def create_user_profile(sender, instance, signal, created, **kwargs):
    
    from django_code.models import UserProfile
    if created:
        UserProfile.objects.create(user=instance)
        # Do other things here if necessary
