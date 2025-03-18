from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import (
    Customer,
    Business,
    BusinessCategory,
    County,
    SubCounty,
    Area,
    Ward,
    Token,
)
from .paginators import UsersPagination
from .serializers import (
    CustomerSerializer,
    CountySerializer,
    SubCountySerializer,
    BusinessSerializer,
    BusinessCategorySerializer,
    AreaSerializer,
    WardSerializer,
)
from utils.token import get_user_from_request, get_customer_from_request
from utils.cache import cache_decorator
from utils.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from rest_framework import status, generics
from django.urls import reverse
from django.contrib.auth.models import User
from django_countries import countries


# Create your views here.


@receiver(post_save, sender=User)
def create_user_auth_token(sender, instance=None, created=False, **kwargs):
    """
    This function is used to create a token for the user when the user is created.
    """
    if created:
        Token.objects.create(user=instance)


@receiver(post_save, sender=Customer)
def create_customer_auth_token(sender, instance=None, created=False, **kwargs):
    """
    This function is used to create a token for the customer when the customer is created.
    This functionality can be utilised for user authentication and is just here as a foundation of the infrastructure.
    """
    if created:
        Token.objects.create(customer=instance)


class StatusView(APIView):
    """
    This class is used to return the status of the API.
    Future versions may include some kind of self check and returns a list of endpoints
    indicationg which are up and which are down.
    """

    def get(self, request):
        json = {"statusCode": status.HTTP_200_OK, "body": "OK"}
        return Response(json)


class CustomerView(generics.GenericAPIView):
    """
    This class is used to handle the CRUD operations on the customer model.
    """

    pagination_class = UsersPagination
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all().order_by("created_at")

    def get(self, request, customer_ulid=None):
        """
        This method is used to get the customer details. It checks for the customer_ulid and returns the customer details if the customer_ulid is provided.
        If the customer_ulid is not provided, it returns the list of customers.

        Parameters:
            request: Request object
            customer_ulid: The ulid of the customer

        Returns:
            Response object

        Note:
            The details are only returned to either the same customer or the staff.
        """
        data = {}
        user, err = get_user_from_request(request)

        if customer_ulid is not None:
            customer = get_object_or_404(Customer, ulid=customer_ulid)

            if (user is not None and user.is_staff) or user == customer:
                serializer = CustomerSerializer(customer)
                data["statusCode"] = status.HTTP_200_OK
                data["body"] = serializer.data
                return Response(data)
            else:
                data["statusCode"] = status.HTTP_403_FORBIDDEN
                data["body"] = (
                    "Forbidden | You do not have permission to access this resource"
                )
                return Response(data, status=status.HTTP_403_FORBIDDEN)
        elif user:
            data["statusCode"] = status.HTTP_200_OK
            data["body"] = user
            return Response(data)
        else:
            page = self.paginate_queryset(self.queryset)
            data = {}
            if page is not None:
                serializer = self.serializer_class(page, many=True)
                data["statusCode"] = status.HTTP_200_OK
                data["body"] = serializer.data
                return self.get_paginated_response(data)
            else:
                data["statusCode"] = status.HTTP_404_NOT_FOUND
                data["body"] = "No more data"
                return Response(data, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, customer_ulid):
        """
        This method is used to delete the customer details.

        Parameters:
            request: Request object
            customer_ulid: The ulid of the customer

        Returns:
            Response object

        Note:
            The details are only deleted by either the same customer or the staff.
        """
        data = {}
        user, err = get_user_from_request(request)
        if user is None:
            user, err = get_customer_from_request(request)
        if err is not None:
            data["statusCode"] = status.HTTP_400_BAD_REQUEST
            data["body"] = str(err)
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        customer = get_object_or_404(Customer, ulid=customer_ulid)
        if (isinstance(user, User) and user.is_staff) or user == customer:
            customer.delete()
            data["statusCode"] = status.HTTP_204_NO_CONTENT
            return Response(data, status.HTTP_204_NO_CONTENT)
        else:
            data["statusCode"] = status.HTTP_403_FORBIDDEN
            data["body"] = (
                "Not Allowed | You still have to explicitly pass the ulid even if there exists an auth token"
            )
            return Response(data, status=status.HTTP_403_FORBIDDEN)

    def post(self, request):
        """
        This method is used to create a new customer.

        Parameters:
            request: Request object

        Returns:
            Response object
        """
        new_customer = CustomerSerializer(data=request.data)
        data = {}
        if new_customer.is_valid():
            new_customer.save()
            data["statusCode"] = status.HTTP_201_CREATED
            data["body"] = new_customer.data
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data["statusCode"] = status.HTTP_400_BAD_REQUEST
            data["body"] = new_customer.errors
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, customer_ulid):
        """
        This method is used to update the customer details.

        Parameters:
            request: Request object
            customer_ulid: The ulid of the customer

        Returns:
            Response object

        Note:
            The details are only updated by either the same customer or the staff.
        """
        data = {}
        user, err = get_user_from_request(request)
        customer = get_object_or_404(Customer, ulid=customer_ulid)
        if (user is not None and user.is_staff) or user == customer:
            serializer = CustomerSerializer(customer, data=request.data)
            if serializer.is_valid():
                serializer.save()
                data["statusCode"] = status.HTTP_200_OK
                data["body"] = serializer.data
                return Response(data)
            else:
                data["statusCode"] = status.HTTP_400_BAD_REQUEST
                data["body"] = serializer.errors
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data["statusCode"] = status.HTTP_403_FORBIDDEN
            data["body"] = (
                "Forbidden | You do not have permission to access this resource"
            )
            return Response(data, status=status.HTTP_403_FORBIDDEN)


class BusinessView(APIView):
    """
    This class is used to handle the CRUD operations on the business model.
    """

    def get(self, request, business_ulid=None):
        """
        This method is used to get the business details. It checks for the business_ulid and returns the business details if the business_ulid is provided.
        If the business_ulid is not provided, it returns the list of businesses.

        Parameters:
            request: Request object
            business_ulid: The ulid of the business

        Returns:
            Response object
        """
        data = {}
        if business_ulid is not None:
            business = get_object_or_404(Business, ulid=business_ulid)
            serializer = BusinessSerializer(business)
            data["statusCode"] = status.HTTP_200_OK
            data["body"] = serializer.data
            return Response(data)
        else:
            businesses = Business.objects.all()
            serializer = BusinessSerializer(businesses, many=True)
            data["statusCode"] = status.HTTP_200_OK
            data["body"] = serializer.data
            return Response(data)

    def post(self, request):
        """
        This method is used to create a new business.

        Parameters:
            request: Request object

        Returns:
            Response object
        """
        new_business = BusinessSerializer(data=request.data)
        data = {}
        if new_business.is_valid():
            new_business.save()
            data["statusCode"] = status.HTTP_201_CREATED
            data["body"] = new_business.data
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data["statusCode"] = status.HTTP_400_BAD_REQUEST
            data["body"] = new_business.errors
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, business_ulid):
        """
        This method is used to delete the business details.

        Parameters:
            request: Request object
            business_ulid: The ulid of the business

        Returns:
            Response object

        Note:
            The details are only deleted by the staff.
        """
        data = {}
        user, err = get_user_from_request(request)
        if err is not None:
            data["statusCode"] = status.HTTP_400_BAD_REQUEST
            data["body"] = str(err)
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        if user.is_staff:
            business = get_object_or_404(Business, ulid=business_ulid)
            business.delete()
            data["statusCode"] = status.HTTP_204_NO_CONTENT
            data["body"] = "Business deleted successfully"
            return Response(data)
        else:
            data["statusCode"] = status.HTTP_403_FORBIDDEN
            data["body"] = (
                "Forbidden | You do not have permission to access this resource"
            )
            return Response(data, status=status.HTTP_403_FORBIDDEN)

    def put(self, request, business_ulid):
        """
        This method is used to update the business details.

        Parameters:
            request: Request object
            business_ulid: The ulid of the business

        Returns:
            Response object
        """
        data = {}
        user, err = get_user_from_request(request)
        business = get_object_or_404(Business, ulid=business_ulid)
        if user.is_staff:
            serializer = BusinessSerializer(business, data=request.data)
            if serializer.is_valid():
                serializer.save()
                data["statusCode"] = status.HTTP_200_OK
                data["body"] = serializer.data
                return Response(data)
            else:
                data["statusCode"] = status.HTTP_400_BAD_REQUEST
                data["body"] = serializer.errors
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data["statusCode"] = status.HTTP_403_FORBIDDEN
            data["body"] = (
                "Forbidden | You do not have permission to access this resource"
            )
            return Response(data, status=status.HTTP_403_FORBIDDEN)


class BusinessCategoryView(APIView):
    """
    This class is used to handle the CRUD operations on the business category model.
    """

    @cache_decorator
    def get(self, request):
        """
        This method is used to get the business categories.

        Parameters:
            request: Request object

        Returns:
            Response object

        Cache:
            The response is cached for 0.1 hours. This is to reduce the load on the server
            because the categories are not expected to change frequently.
        """
        categories = BusinessCategory.objects.all()
        serializer = BusinessCategorySerializer(categories, many=True)
        data = {"statusCode": status.HTTP_200_OK, "body": serializer.data}
        return Response(data)

    def post(self, request):
        """
        This method is used to create a new business category.
        """
        data = {}
        new_category = BusinessCategorySerializer(data=request.data)
        if new_category.is_valid():
            new_category.save()
            data["statusCode"] = status.HTTP_201_CREATED
            data["body"] = new_category.data
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data["statusCode"] = status.HTTP_400_BAD_REQUEST
            data["body"] = new_category.errors
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class CountyView(APIView):
    """
    This class is used to handle the CRUD operations on the county model.
    """

    @cache_decorator
    def get(self, request, county_name=None):
        """
        This method is used to get the county details.

        Parameters:
            request: Request object
            county_name: The name of the county

        Returns:
            Response object

        Cache:
            The response is cached for 0.1 hours. This is to reduce the load on the server
            because the counties are not expected to change frequently.
        """
        if county_name is not None:
            county = get_object_or_404(County, name__iexact=county_name)
            serializer = CountySerializer(county)
            data = {"statusCode": status.HTTP_200_OK, "body": serializer.data}
            return Response(data)
        else:
            counties = County.objects.all()
            serializer = CountySerializer(counties, many=True)
            data = {"statusCode": status.HTTP_200_OK, "body": serializer.data}
            return Response(data)

    def post(self, request):
        new_county = CountySerializer(data=request.data)
        data = {}
        if new_county.is_valid():
            new_county.save()
            data["statusCode"] = status.HTTP_201_CREATED
            data["body"] = new_county.data
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data["statusCode"] = status.HTTP_400_BAD_REQUEST
            data["body"] = new_county.errors
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class SubCountyView(APIView):
    """
    This class is used to handle the CRUD operations on the subcounty model.
    """

    @cache_decorator
    def get(self, request, county_name, subcounty_name=None):
        """
        This method is used to get the subcounty details.
        It checks for the subcounty_name and returns the subcounty details if the subcounty_name is provided.

        Parameters:
            request: Request object
            county_name: The name of the county
            subcounty_name: The name of the subcounty

        Returns:
            Response object

        Cache:
            The response is cached for 0.1 hours. This is to reduce the load on the server
            because the subcounties are not expected to change frequently.
        """
        if subcounty_name is not None:
            sub_county = get_object_or_404(
                SubCounty, name__iexact=subcounty_name, county__name__iexact=county_name
            )
            serializer = SubCountySerializer(sub_county)
            data = {"statusCode": status.HTTP_200_OK, "body": serializer.data}
            return Response(data)
        else:
            sub_counties = SubCounty.objects.filter(county__name__iexact=county_name)
            serializer = SubCountySerializer(sub_counties, many=True)
            data = {"statusCode": status.HTTP_200_OK, "body": serializer.data}
            return Response(data)

    def post(self, request, county_name):
        """
        This method is used to create a new subcounty.
        """
        new_sub_county = SubCountySerializer(data=request.data.copy())
        new_sub_county.initial_data["county_name"] = county_name
        data = {}
        if new_sub_county.is_valid():
            new_sub_county.save()
            data["statusCode"] = status.HTTP_201_CREATED
            data["body"] = new_sub_county.data
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data["statusCode"] = status.HTTP_400_BAD_REQUEST
            data["body"] = new_sub_county.errors
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class WardView(APIView):
    """
    This class is used to handle the CRUD operations on the ward model.
    """

    @cache_decorator
    def get(self, request, county_name, subcounty_name, ward_name=None):
        if ward_name is not None:
            ward = get_object_or_404(
                Ward,
                name__iexact=ward_name,
                sub_county__county__name__iexact=county_name,
                sub_county__name__iexact=subcounty_name,
            )
            serializer = WardSerializer(ward)
            data = {"statusCode": status.HTTP_200_OK, "body": serializer.data}
            return Response(data)
        else:
            wards = Ward.objects.filter(
                sub_county__county__name__iexact=county_name,
                sub_county__name__iexact=subcounty_name,
            )
            serializer = WardSerializer(wards, many=True)
            data = {"statusCode": status.HTTP_200_OK, "body": serializer.data}
            return Response(data)

    def post(self, request, county_name, subcounty_name):
        new_ward = WardSerializer(data=request.data.copy())
        new_ward.initial_data["sub_county_name"] = subcounty_name
        new_ward.initial_data["county_name"] = county_name
        data = {}

        if new_ward.is_valid():
            new_ward.save()
            data["statusCode"] = status.HTTP_201_CREATED
            data["body"] = new_ward.data
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data["statusCode"] = status.HTTP_400_BAD_REQUEST
            data["body"] = new_ward.errors
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class AreaView(APIView):
    """
    This class is used to handle the CRUD operations on the area model.
    """

    @cache_decorator
    def get(self, request, county_name, subcounty_name, ward_name, area_name=None):
        """
        This method is used to get the area details.
        It checks for the area_name and returns the area details if the area_name is provided
        and then returns the list of areas if the area_name otherwise.

        Parameters:
            request: Request object
            county_name: The name of the county
            subcounty_name: The name of the subcounty
            ward_name: The name of the ward
            area_name: The name of the area

        Returns:
            Response object

        Cache:
            The response is cached for 0.1 hours. This is to reduce the load on the server
            because the areas are not expected to change frequently.
            And yes I repeated that statement verbose all these times
        """
        if area_name is not None:
            area = get_object_or_404(
                Area,
                name__iexact=area_name,
                ward__sub_county__county__name__iexact=county_name,
                ward__sub_county__name__iexact=subcounty_name,
                ward__name__iexact=ward_name,
            )
            serializer = AreaSerializer(area)
            data = {"statusCode": status.HTTP_200_OK, "body": serializer.data}
            return Response(data)
        else:
            areas = Area.objects.filter(
                ward__sub_county__county__name__iexact=county_name,
                ward__sub_county__name__iexact=subcounty_name,
                ward__name__iexact=ward_name,
            )
            serializer = AreaSerializer(areas, many=True)
            data = {"statusCode": status.HTTP_200_OK, "body": serializer.data}
            return Response(data)

    def post(self, request, county_name, subcounty_name, ward_name):
        new_location = AreaSerializer(data=request.data.copy())
        new_location.initial_data["ward_name"] = ward_name
        new_location.initial_data["sub_county_name"] = subcounty_name
        new_location.initial_data["county_name"] = county_name
        data = {}
        if new_location.is_valid():
            new_location.save()
            data["statusCode"] = status.HTTP_201_CREATED
            data["body"] = new_location.data
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data["statusCode"] = status.HTTP_400_BAD_REQUEST
            data["body"] = new_location.errors
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_business_customers(request, business_ulid):
    """
    This utility function is used to get the customers of a business.

    Parameters:
        request: Request object
        business_ulid: The ulid of the business

    Returns:
        Response object
    """
    customers = get_object_or_404(Business, ulid=business_ulid).customers.all()
    serializer = CustomerSerializer(customers, many=True)
    data = {"statusCode": status.HTTP_200_OK, "body": serializer.data}

    return Response(data)


@api_view(["GET"])
def get_customer_businesses(request):
    """
    This utility function is used to get the businesses of a user.

    Parameters:
        request: Request object
    """
    data = {}
    user, err = get_user_from_request(request)
    if err is not None:
        data["statusCode"] = status.HTTP_400_BAD_REQUEST
        data["body"] = str(err)
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    businesses = Business.objects.filter(customers__in=[user])
    serializer = BusinessSerializer(businesses, many=True)
    data["statusCode"] = status.HTTP_200_OK
    data["body"] = serializer.data
    return Response(data)


@api_view(["GET"])
def get_nationalities(request):
    """
    This utility function is used to get the list of nationalities.

    Returns:
        Response object
    """
    country_list = list(countries)
    data = {"statusCode": status.HTTP_200_OK, "body": country_list}
    return Response(data)


@api_view(["POST", "PUT"])
def send_data_deletion_link(request, customer_ulid):
    """
    This utility function is used to send the data deletion link to the customer.

    Parameters:
        request: Request object
        customer_ulid: The ulid of the customer

    Returns:
        Response object
    """
    data = {}
    customer = get_object_or_404(Customer, ulid=customer_ulid)
    user, err = get_customer_from_request(request)
    if err is not None:
        data["statusCode"] = status.HTTP_400_BAD_REQUEST
        data["body"] = str(err)
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    origin = request.data.get("origin")
    if origin is None:
        data["statusCode"] = status.HTTP_400_BAD_REQUEST
        data["body"] = "Origin is required"
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    if origin[-1] != "/":
        origin += "/"

    if user == customer:
        token = customer.token
        link = f"{origin}{reverse('api:confirm_delete_customer', args=[token])}"
        send_mail(
            subject="Request for data deletion",
            body=f"Click the link below to delete your data\n{link}",
            destination=customer.email,
        )
        data["statusCode"] = status.HTTP_200_OK
        data["body"] = "Data deletion link sent successfully"
        return Response(data)
    else:
        data["statusCode"] = status.HTTP_403_FORBIDDEN
        data["body"] = "Forbidden | You do not have permission to access this resource"
        return Response(data, status=status.HTTP_403_FORBIDDEN)


@api_view(["GET"])
def delete_customer(request, token):
    """
    This utility function is used to delete the customer.

    Parameters:
        request: Request object
        token: The token of the customer

    Returns:
        Response object
    """
    data = {}
    customer = get_object_or_404(Token, key=token).customer

    if customer is not None:
        customer.delete()
        data["statusCode"] = status.HTTP_200_OK
        data["body"] = "Customer deleted successfully"
        return Response(data)
    else:
        data["statusCode"] = status.HTTP_404_NOT_FOUND
        data["body"] = "Customer not found"
        return Response(data, status=status.HTTP_404_NOT_FOUND)
