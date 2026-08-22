import { patch } from "@web/core/utils/patch";
import { ProductPage } from "@pos_self_order/app/pages/product_page/product_page";

function isProductCategoryAvailable(selfOrder, product) {
    if (product.pos_categ_ids.length === 0) {
        return true;
    }
    return product.pos_categ_ids.some((category) => selfOrder.isCategoryAvailable(category.id));
}

function canOpenInProductPage(selfOrder, product) {
    return (
        product &&
        product.self_order_available &&
        !product.isCombo() &&
        !selfOrder.isProductSnoozed(product) &&
        isProductCategoryAvailable(selfOrder, product)
    );
}

function getProductsForCategory(selfOrder, category) {
    return category?.associatedProducts || selfOrder.productByCategIds[category?.id] || [];
}

patch(ProductPage.prototype, {
    hasMissingAttributeValues() {
        if (!this.productTemplate.attribute_line_ids.length) {
            return false;
        }
        return super.hasMissingAttributeValues(...arguments);
    },

    get productNavigationList() {
        if (!this.selfOrder.availableCategories.length) {
            this.selfOrder.computeAvailableCategories();
        }

        let products = getProductsForCategory(this.selfOrder, this.selfOrder.currentCategory);

        if (!products.some((product) => product.id === this.productTemplate.id)) {
            const productCategory = this.productTemplate.pos_categ_ids.find(
                (category) =>
                    this.selfOrder.isCategoryAvailable(category.id) &&
                    getProductsForCategory(this.selfOrder, category).some(
                        (product) => product.id === this.productTemplate.id
                    )
            );
            if (productCategory) {
                this.selfOrder.currentCategory = productCategory;
                products = getProductsForCategory(this.selfOrder, productCategory);
            } else {
                products = this.selfOrder.models["product.template"].getAll();
            }
        }

        return products.filter((product) => canOpenInProductPage(this.selfOrder, product));
    },

    get currentNavigationIndex() {
        return this.productNavigationList.findIndex(
            (product) => product.id === this.productTemplate.id
        );
    },

    get hasPreviousProduct() {
        return this.currentNavigationIndex > 0;
    },

    get hasNextProduct() {
        const index = this.currentNavigationIndex;
        return index >= 0 && index < this.productNavigationList.length - 1;
    },

    navigateToProductOffset(offset) {
        const products = this.productNavigationList;
        const index = this.currentNavigationIndex;
        const nextProduct = products[index + offset];
        if (!nextProduct) {
            return;
        }
        delete this.state.selectedValues[nextProduct.id];
        this.router.navigate("product", { id: nextProduct.id });
    },

    previousProduct() {
        this.navigateToProductOffset(-1);
    },

    nextProduct() {
        this.navigateToProductOffset(1);
    },
});
