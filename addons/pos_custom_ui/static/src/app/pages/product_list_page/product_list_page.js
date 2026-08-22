import { patch } from "@web/core/utils/patch";
import { ProductListPage } from "@pos_self_order/app/pages/product_list_page/product_list_page";
import { scrollItemIntoViewX } from "@pos_self_order/app/utils/scroll";

patch(ProductListPage.prototype, {
    get useNestedCategoryNavigation() {
        return true;
    },

    selectCategory(category) {
        this.state.selectedCategory = category;
        if (this.useNestedCategoryNavigation) {
            if (!category.parent_id) {
                this.toggleSubCategoryPanel();
            }
            this.ensureCategoryVisible();
            this.productListRef.el?.scrollTo({ top: 0 });
        } else {
            this.scrollToCategory(category.id);
        }
    },

    ensureCategoryVisible() {
        if (!this.useNestedCategoryNavigation) {
            return;
        }

        scrollItemIntoViewX(
            this.categoryListRef.el,
            `[data-category-pill="${this.selectedCategory.id}"]`,
            { edgePadding: 20, minRightGap: this.categoryListRef.el.offsetWidth / 3 }
        );
    },

    getSubCategories() {
        if (!this.useNestedCategoryNavigation) {
            return [];
        }

        const currentCategory = this.state.selectedCategory;
        if (!currentCategory) {
            return [];
        }
        if (currentCategory.parent_id) {
            return currentCategory.parent_id.child_ids;
        }
        return currentCategory.child_ids || [];
    },

    get productCategories() {
        if (this.useNestedCategoryNavigation) {
            return [this.selectedCategory];
        }
        return this.state.topCategories;
    },

    toggleSubCategoryPanel() {
        if (!this.useNestedCategoryNavigation) {
            return;
        }

        const el = this.subCategoryContainerRef.el;
        const nextSubCategories = this.getSubCategories();
        if (this.state.subCategories.length > 0 && nextSubCategories.length === 0) {
            el.classList.remove("show");
            const oldSelectedCat = this.selectedCategory;
            const self = this;
            el.addEventListener("transitionend", function handler(e) {
                if (oldSelectedCat === self.selectedCategory) {
                    self.state.subCategories = [];
                }
                el.removeEventListener("transitionend", handler);
            });
            return;
        } else if (nextSubCategories.length === 0 && this.state.subCategories.length === 0) {
            return;
        }

        this.state.subCategories = nextSubCategories;
        el.classList.add("show");
    },
});
